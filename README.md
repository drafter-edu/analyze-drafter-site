# analyze_drafter_site

[![codecov](https://codecov.io/gh/drafter-edu/analyze-drafter-site/branch/main/graph/badge.svg?token=analyze-drafter-site_token_here)](https://codecov.io/gh/drafter-edu/analyze-drafter-site)
[![CI](https://github.com/drafter-edu/analyze-drafter-site/actions/workflows/main.yml/badge.svg)](https://github.com/drafter-edu/analyze-drafter-site/actions/workflows/main.yml)

A Python tool for analyzing and summarizing Drafter websites in various ways, to simplify grading.

## Install it from PyPI

```bash
pip install analyze_drafter_site
```

## Usage

### Command Line Interface

Analyze a Drafter website Python file:

```bash
$ python -m analyze_drafter_site path/to/site.py
# or
$ analyze_drafter_site path/to/site.py
```

### Output Formats

By default, the tool outputs to stdout and creates three files:
- `analysis.csv` - All complexity and dataclass data in CSV format
- `analysis.mmd` - Mermaid class diagram and function call graph
- `analysis.html` - Full HTML report with tables and rendered diagrams

### Command Line Options

```bash
$ analyze_drafter_site --help

Options:
  --csv / --no-csv          Output CSV data to file (default: on)
  --csv-file TEXT           CSV output filename (default: analysis.csv)
  --mermaid / --no-mermaid  Output Mermaid diagrams to file (default: on)
  --mermaid-file TEXT       Mermaid output filename (default: analysis.mmd)
  --html / --no-html        Output HTML report to file (default: on)
  --html-file TEXT          HTML output filename (default: analysis.html)
  --stdout / --no-stdout    Output plain text to stdout (default: on)
```

### Examples

Generate only HTML output with custom filename:
```bash
$ analyze_drafter_site site.py --no-csv --no-mermaid --html-file report.html
```

Generate all outputs with custom filenames:
```bash
$ analyze_drafter_site site.py \
  --csv-file results.csv \
  --mermaid-file diagrams.mmd \
  --html-file report.html
```

Disable stdout, only generate files:
```bash
$ analyze_drafter_site site.py --no-stdout
```

### Programmatic Usage

```py
from analyze_drafter_site import Analyzer, calculate_complexity

# Read your code
with open('site.py') as f:
    code = f.read()

# Calculate complexity
tree, complexity_by_section = calculate_complexity(code)

# Analyze details
analyzer = Analyzer()
analyzer.analyze(code)

# Access results
print(analyzer.get_dataclass_attribute_csv())
print(analyzer.generate_mermaid_class_diagram())
```

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
