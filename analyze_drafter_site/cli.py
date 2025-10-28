"""CLI interface for analyze_drafter_site

This module provides a CLI interface for analyzing Drafter websites.

First parameter is the path to the Python file to analyze.
"""

import click
from analyze_drafter_site import Analyzer, calculate_complexity


@click.command()
@click.argument("path", type=click.Path(exists=True))
def main(path):
    """Analyze a Drafter website."""
    with open(path) as f:
        code = f.read()
    analyzer = Analyzer()
    analyzer.analyze(code)
    for result in analyzer.save_as_string():
        print(result)

    tree, complexity_by_section = calculate_complexity(code)
    print("\nComplexity Analysis:")
    for section in complexity_by_section:
        print(f"Function: {section['name']}")
        print(section["score"])


if __name__ == "__main__":
    main()
