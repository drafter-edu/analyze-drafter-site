import ast
from dataclasses import dataclass
from analyze_drafter_site.complexity.diagnostics import Diagnostics


REMOVE_CHAR = " "


@dataclass
class StringLiteralLocation:
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    is_expr: bool
    value: str

    def is_on_line(self, line):
        return self.start_line <= line <= self.end_line

    def is_in_column(self, col):
        return self.start_col <= col <= self.end_col

    def has_position(self, line_number, column_number):
        if self.start_line <= line_number <= self.end_line:
            if self.start_col <= column_number <= self.end_col:
                return True
        return False

    def extract(self, line_number, code_line):
        start_column = 0
        end_column = len(code_line)
        if line_number == self.start_line:
            start_column = self.start_col
        if line_number == self.end_line:
            end_column = self.end_col
        return code_line[start_column:end_column]

    def extract_outside(self, line_number, code_line):
        start_column = 0
        end_column = len(code_line)
        if line_number == self.start_line:
            start_column = self.start_col
        if line_number == self.end_line:
            end_column = self.end_col
        if start_column < end_column:
            spacer = REMOVE_CHAR * (end_column - start_column)
        else:
            spacer = ""
        return code_line[:start_column] + spacer + code_line[end_column:]


class StringWalker(ast.NodeVisitor):
    def __init__(self):
        self.strings: dict[bool, list[StringLiteralLocation]] = {True: [], False: []}
        self.inside_expr = False

    def track_node(self, node, value):
        self.strings[self.inside_expr].append(
            StringLiteralLocation(
                node.lineno - 1,
                node.end_lineno - 1,
                node.col_offset,
                node.end_col_offset,
                self.inside_expr,
                value,
            )
        )

    def visit_Str(self, node):
        self.track_node(node, node.s)
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            self.track_node(node, node.value)
        self.generic_visit(node)

    def visit_JoinedStr(self, node):
        for value in node.values:
            self.visit(value)
        self.track_node(node, f"JoinedStr({len(node.values)})")
        self.generic_visit(node)

    def visit_FormattedValue(self, node):
        self.visit(node.value)
        self.generic_visit(node)

    # def visit_Tuple(self, node):
    #    if len(node.elts) == 1:
    #        self.visit(node.elts[0])

    def visit_Expr(self, node):
        self.inside_expr = isinstance(
            node.value, (ast.Str, ast.Constant, ast.JoinedStr, ast.FormattedValue)
        )
        self.generic_visit(node)
        self.inside_expr = False


def remove_user_text(tree: ast.AST, code: str, diagnostics: Diagnostics):
    # Walk the AST to find string literals
    string_walker = StringWalker()
    try:
        string_walker.visit(tree)
    except Exception as e:
        diagnostics.add_exception(
            "Failed while removing string literals.",
            e,
        )
        raise e
    keep_strings = string_walker.strings[False]
    remove_strings = string_walker.strings[True]

    # find all the hashes in the code, get them until the end of their line
    hashes = {}
    for i, line in enumerate(code.splitlines()):
        if "#" in line:
            start = line.index("#")
            end = len(line)
            if i not in hashes:
                hashes[i] = []
            hashes[i].append((start, end))

    # Remove hashes and string literal expressions from the code
    lines = code.splitlines()
    kept = []
    for i, line in enumerate(lines):
        # If there's a hash here, then we remove that chunk
        # UNLESS it's in a keep_strings string
        # And we also remove it if it's in a remove_strings string
        for remove_string in remove_strings:
            if remove_string.is_on_line(i):
                # print("<<<", line, remove_string)
                line = remove_string.extract_outside(i, line)
                # print(">>>", line, i)
        if i in hashes:
            for start, end in hashes[i]:
                # If the hash is in a safe string literal, we don't remove it
                # print(">>>", start, end, i, repr(lines[i][start:end]))
                if any(
                    keep_string.has_position(i, start) for keep_string in keep_strings
                ):
                    continue
                line = line[:start] + REMOVE_CHAR * (end - start) + line[end:]
        kept.append(line)

    return "\n".join(kept)
