import ast
from analyze_drafter_site.complexity.diagnostics import Diagnostics


class ExtentGetter(ast.NodeVisitor):
    def __init__(self):
        self.extents = None

    def check_all(self, node):
        self.extents = [
            node.lineno,
            node.col_offset,
            node.end_lineno,
            node.end_col_offset,
        ]
        self.visit(node)

    def visit(self, node: ast.AST):
        """
        Visits a node and updates the extents accordingly.
        This relies on a try/catch approach because not all nodes have
        the lineno, col_offset, end_lineno, and end_col_offset attributes.
        This varies across different Python versions and platforms.

        Args:
            node (ast.AST): The AST node to visit.
        """
        if self.extents is None:
            self.extents = [
                node.lineno,  # type: ignore
                node.col_offset,  # type: ignore
                node.end_lineno,  # type: ignore
                node.end_col_offset,  # type: ignore
            ]
        try:
            if self.extents[0] > node.lineno:  # type: ignore
                self.extents[0] = node.lineno  # type: ignore
                self.extents[1] = node.col_offset  # type: ignore
            elif self.extents[0] == node.lineno:  # type: ignore
                if self.extents[1] > node.col_offset:  # type: ignore
                    self.extents[1] = node.col_offset  # type: ignore
            if self.extents[2] < node.end_lineno:  # type: ignore
                self.extents[2] = node.end_lineno  # type: ignore
                self.extents[3] = node.end_col_offset  # type: ignore
            elif self.extents[2] == node.end_lineno:  # type: ignore
                if self.extents[3] < node.end_col_offset:  # type: ignore
                    self.extents[3] = node.end_col_offset  # type: ignore
        except Exception:
            pass
        ast.NodeVisitor.visit(self, node)

    def visit_JoinedStr(self, node):
        return None


def get_extents(node, diagnostics: Diagnostics):
    try:
        extenter = ExtentGetter()
        extenter.check_all(node)
    except Exception as e:
        diagnostics.add_exception("Failed to get extents of the string.", e)
        raise e
    return extenter.extents
