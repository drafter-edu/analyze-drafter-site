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
    tree, complexity_by_section = calculate_complexity(code)
    print("\nComplexity Analysis:")
    categories = sorted(AST_CATEGORY_ORDER, key=lambda x: -x[1])
    longest_name = (
        max(len(section["name"]) for section in complexity_by_section)
        if complexity_by_section
        else 4
    )
    print(
        "Name".ljust(longest_name),
        "Start".ljust(6),
        "End".ljust(6),
        "Total".rjust(6),
        "|",
        *[cat.title() + " " for cat, order in categories],
        sep="\t"
    )
    for section in complexity_by_section:
        score = section["score"]
        parts = [
            str(score["parts"][category]).ljust(1 + len(category))
            for category, order in categories
        ]
        line = [
            section["name"].ljust(longest_name),
            str(section["startLine"]).ljust(6),
            str(section["endLine"]).ljust(6),
            str(score["total"]).rjust(6),
            "|",
        ]
        line.extend(parts)
        print("\t".join(str(x) for x in line))
    print("---" * 20)
    print("Detailed Analysis:")
    analyzer = Analyzer()
    analyzer.analyze(code)
    for result in analyzer.save_as_string():
        print(result)


if __name__ == "__main__":
    main()
