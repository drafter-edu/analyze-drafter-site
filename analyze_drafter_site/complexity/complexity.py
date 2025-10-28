import sys
import ast
from analyze_drafter_site.complexity.extents import get_extents
from analyze_drafter_site.complexity.strings import remove_user_text
from analyze_drafter_site.complexity.score_loader import (
    AST_SCORE_CATEGORIES,
    NAME_SCORE_CATEGORIES,
    AST_CATEGORY_ORDER,
)
from analyze_drafter_site.complexity.diagnostics import Diagnostics


def remove_blank_lines(lines):
    return "\n".join(line for line in lines if line.strip())


def select_node(node, source, extents, diagnostics: Diagnostics):
    # TODO: Remove comments, string literal expression values
    lines = source.splitlines()
    try:
        score = score_node(node)
    except Exception as e:
        diagnostics.add_exception("Failed while selecting functions.", e)
        raise e
    return {
        "code": remove_blank_lines(lines[extents[0] - 1 : extents[2]]),
        # if next_lineno is not None else lines[node.lineno - 1:],
        "startLine": extents[0] - 1,
        "endLine": extents[2] + 1,
        "score": score,
        "name": node.name,
    }


class ASTCalculator(ast.NodeVisitor):
    SCORE_CATEGORIES = ["unusual", "important", "mundane", "drafter"]

    def __init__(self):
        self.asts = {
            kind: 0 for kinds in AST_SCORE_CATEGORIES.values() for kind in kinds
        }
        self.scores = {category: 0 for category in AST_SCORE_CATEGORIES}

        for category, kinds in AST_SCORE_CATEGORIES.items():
            for kind in kinds:
                setattr(self, f"visit_{kind}", self.make_score_changer(kind, category))

    def make_score_changer(self, kind, category):
        if sys.platform == "skulpt":

            def score_changer(self, node):
                self.scores[category] += 1
                self.asts[kind] += 1
                self.generic_visit(node)

        else:

            def score_changer(node):
                self.scores[category] += 1
                self.asts[kind] += 1
                self.generic_visit(node)

        return score_changer

    def visit_Name(self, node):
        if node.id in NAME_SCORE_CATEGORIES:
            category = NAME_SCORE_CATEGORIES[node.id]
            self.scores[category] += 1
        self.generic_visit(node)

    def finalize(self):
        total = 0
        for category, weight in AST_CATEGORY_ORDER:
            total += self.scores[category] * weight
        return {
            "total": total / 1000,
            "parts": self.scores,
        }


def score_node(node):
    calculator = ASTCalculator()
    calculator.visit(node)
    return calculator.finalize()


def calculate_complexity(code: str):
    diagnostics = Diagnostics()

    # Parse the code into an AST
    try:
        tree = ast.parse(code, "submitted_code.py")
    except Exception as e:
        diagnostics.add_exception(
            "Failed to parse code. Please check for syntax errors.", e
        )
        raise e

    cleaned_code = remove_user_text(tree, code, diagnostics)

    # Iterate through the top-level statements looking for routes
    sections = []
    if isinstance(tree, ast.Module):
        following_nodes = tree.body[1:] + [None]
        for node, next_node in zip(tree.body, following_nodes):
            if isinstance(node, ast.FunctionDef):
                extents = get_extents(node, diagnostics)
                sections.append(select_node(node, cleaned_code, extents, diagnostics))

    return tree, sections
