"""CLI interface for analyze_drafter_site

This module provides a CLI interface for analyzing Drafter websites.

First parameter is the path to the Python file to analyze.
"""

import click
from analyze_drafter_site import Analyzer, calculate_complexity, AST_CATEGORY_ORDER


def generate_complexity_csv(complexity_by_section):
    """Generate CSV format for complexity analysis."""
    lines = ["Name,Start,End,Total,Unusual,Important,Good,Mundane,Drafter"]
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
        lines.append(",".join(line))
    return "\n".join(lines)


def generate_all_csv(complexity_by_section, analyzer):
    """Generate complete CSV output with all tabular data."""
    parts = [
        generate_complexity_csv(complexity_by_section),
        analyzer.get_dataclass_attribute_csv(),
        analyzer.get_dataclass_complexity_csv(),
    ]
    return "\n\n".join(parts)


def generate_all_mermaid(analyzer):
    """Generate complete Mermaid output with both diagrams."""
    return f"{analyzer.generate_mermaid_class_diagram()}\n\n{analyzer.generate_mermaid_function_diagram()}"


def generate_html_output(complexity_by_section, analyzer):
    """Generate HTML output with tables and embedded Mermaid rendering."""
    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "    <title>Drafter Site Analysis</title>",
        '    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">',
        '    <script type="module">',
        '        import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";',
        "        mermaid.initialize({ startOnLoad: true });",
        "    </script>",
        "</head>",
        "<body>",
        "    <h1>Drafter Site Analysis</h1>",
        "",
        "    <h2>Complexity Analysis</h2>",
        "    <table>",
        "        <thead>",
        "            <tr>",
        "                <th>Name</th><th>Start</th><th>End</th><th>Total</th>",
        "                <th>Unusual</th><th>Important</th><th>Good</th><th>Mundane</th><th>Drafter</th>",
        "            </tr>",
        "        </thead>",
        "        <tbody>",
    ]

    categories = sorted(AST_CATEGORY_ORDER, key=lambda x: -x[1])
    for section in complexity_by_section:
        score = section["score"]
        parts = [str(score["parts"][category]) for category, order in categories]
        html_parts.append("            <tr>")
        html_parts.append(f'                <td>{section["name"]}</td>')
        html_parts.append(f'                <td>{section["startLine"]}</td>')
        html_parts.append(f'                <td>{section["endLine"]}</td>')
        html_parts.append(f'                <td>{score["total"]}</td>')
        for part in parts:
            html_parts.append(f"                <td>{part}</td>")
        html_parts.append("            </tr>")

    html_parts.extend(
        [
            "        </tbody>",
            "    </table>",
            "",
            "    <h2>Dataclass Attributes</h2>",
        ]
    )

    # Convert CSV to HTML table for dataclass attributes
    attr_csv = analyzer.get_dataclass_attribute_csv()
    attr_lines = attr_csv.strip().split("\n")
    if attr_lines:
        header = attr_lines[0].split(",")
        html_parts.extend(
            [
                "    <table>",
                "        <thead>",
                "            <tr>",
            ]
        )
        for col in header:
            html_parts.append(f"                <th>{col}</th>")
        html_parts.extend(
            [
                "            </tr>",
                "        </thead>",
                "        <tbody>",
            ]
        )
        for line in attr_lines[1:]:
            if line.strip():
                cols = line.split(",")
                html_parts.append("            <tr>")
                for col in cols:
                    html_parts.append(f"                <td>{col}</td>")
                html_parts.append("            </tr>")
        html_parts.extend(
            [
                "        </tbody>",
                "    </table>",
            ]
        )

    html_parts.append("")
    html_parts.append("    <h2>Dataclass Complexity</h2>")

    # Convert CSV to HTML table for complexity scores
    complexity_csv = analyzer.get_dataclass_complexity_csv()
    complexity_lines = complexity_csv.strip().split("\n")
    if complexity_lines:
        header = complexity_lines[0].split(",")
        html_parts.extend(
            [
                "    <table>",
                "        <thead>",
                "            <tr>",
            ]
        )
        for col in header:
            html_parts.append(f"                <th>{col}</th>")
        html_parts.extend(
            [
                "            </tr>",
                "        </thead>",
                "        <tbody>",
            ]
        )
        for line in complexity_lines[1:]:
            if line.strip():
                cols = line.split(",")
                html_parts.append("            <tr>")
                for col in cols:
                    html_parts.append(f"                <td>{col}</td>")
                html_parts.append("            </tr>")
        html_parts.extend(
            [
                "        </tbody>",
                "    </table>",
            ]
        )

    # Add warnings if present
    warnings = analyzer.get_unused_warnings()
    if warnings:
        html_parts.extend(
            [
                "",
                "    <h2>Warnings</h2>",
                "    <pre>",
                warnings,
                "    </pre>",
            ]
        )

    # Add textual details
    html_parts.extend(
        [
            "",
            "    <h2>Details</h2>",
            "    <pre>",
            analyzer.get_textual_details(),
            "    </pre>",
        ]
    )

    # Add Mermaid diagrams
    html_parts.extend(
        [
            "",
            "    <h2>Class Diagram</h2>",
            '    <div class="mermaid">',
            analyzer.generate_mermaid_class_diagram(),
            "    </div>",
            "",
            "    <h2>Function Call Graph</h2>",
            '    <div class="mermaid">',
            analyzer.generate_mermaid_function_diagram(),
            "    </div>",
            "",
            "</body>",
            "</html>",
        ]
    )

    return "\n".join(html_parts)


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--csv/--no-csv", default=True, help="Output CSV data to file")
@click.option("--csv-file", default="analysis.csv", help="CSV output filename")
@click.option(
    "--mermaid/--no-mermaid", default=True, help="Output Mermaid diagrams to file"
)
@click.option("--mermaid-file", default="analysis.mmd", help="Mermaid output filename")
@click.option("--html/--no-html", default=True, help="Output HTML report to file")
@click.option("--html-file", default="analysis.html", help="HTML output filename")
@click.option("--stdout/--no-stdout", default=True, help="Output plain text to stdout")
def main(path, csv, csv_file, mermaid, mermaid_file, html, html_file, stdout):
    """Analyze a Drafter website."""
    with open(path, encoding="utf-8") as f:
        code = f.read()

    # Calculate complexity
    tree, complexity_by_section = calculate_complexity(code)

    # Analyze details
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Generate outputs
    if csv:
        csv_content = generate_all_csv(complexity_by_section, analyzer)
        with open(csv_file, "w", encoding="utf-8") as f:
            f.write(csv_content)

    if mermaid:
        mermaid_content = generate_all_mermaid(analyzer)
        with open(mermaid_file, "w", encoding="utf-8") as f:
            f.write(mermaid_content)

    if html:
        html_content = generate_html_output(complexity_by_section, analyzer)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    if stdout:
        # ===== CSV DATA SECTION (all tabular/empirical data) =====

        # 1. Complexity Analysis in CSV format
        print(generate_complexity_csv(complexity_by_section))

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
