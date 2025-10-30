"""CLI interface for analyze_drafter_site

This module provides a CLI interface for analyzing Drafter websites.

First parameter is the path to the Python file to analyze.
"""

import click
from analyze_drafter_site import Analyzer, calculate_complexity, AST_CATEGORY_ORDER


@click.command()
@click.argument("path", type=click.Path(exists=True))
def main(path):
    """Analyze a Drafter website."""
    with open(path, encoding="utf-8") as f:
        code = f.read()

    # Calculate complexity
    tree, complexity_by_section = calculate_complexity(code)

    # Analyze details
    analyzer = Analyzer()
    analyzer.analyze(code)

    # ===== CSV DATA SECTION (all tabular/empirical data) =====

    # 1. Complexity Analysis in CSV format
    print("Name,Start,End,Total,Unusual,Important,Good,Mundane,Drafter")
    categories = sorted(AST_CATEGORY_ORDER, key=lambda x: -x[1])
    for section in complexity_by_section:
        score = section["score"]
        parts = [str(score["parts"][category]) for category, order in categories]
        line = [
            section["name"],
            str(section["startLine"]),
            str(section["endLine"]),
            str(score["total"]),
        ]
        line.extend(parts)
        print(",".join(line))

    print("-" * 80)

    # 2. Dataclass attribute details (CSV)
    print(analyzer.get_dataclass_attribute_csv())

    print("-" * 80)

    # 3. Dataclass complexity scores (CSV)
    print(analyzer.get_dataclass_complexity_csv())

    print("-" * 80)

    # ===== TEXTUAL RESULTS SECTION =====

    # 4. Warnings about unused dataclasses/attributes
    warnings = analyzer.get_unused_warnings()
    if warnings:
        print(warnings)
        print("-" * 80)

    # 5. Other textual details (Routes, Dataclasses list)
    print(analyzer.get_textual_details())

    print("-" * 80)

    # ===== DIAGRAMS SECTION =====

    # 6. Mermaid diagrams
    print(analyzer.generate_mermaid_class_diagram())
    print()
    print(analyzer.generate_mermaid_function_diagram())


if __name__ == "__main__":
    main()
