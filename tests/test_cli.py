"""Tests for the CLI interface and output format."""

from click.testing import CliRunner
from analyze_drafter_site.cli import main


def test_cli_output_structure(shared_datadir):
    """Test that CLI output has correct structure with sections separated by dashes."""
    basic_file = shared_datadir / "basic.py"

    runner = CliRunner()
    result = runner.invoke(main, [str(basic_file)])

    assert result.exit_code == 0
    output = result.output

    # Split by dash separators
    sections = output.split("-" * 80)

    # Should have at least 5 sections (CSV complexity, CSV attributes, CSV scores, textual, diagrams)
    assert len(sections) >= 5

    # First section should be complexity CSV
    assert "Name,Start,End,Total" in sections[0]

    # Second section should be dataclass attributes CSV
    assert "Dataclass,Attribute,Type,Usage Count,Complexity" in sections[1]

    # Third section should be complexity scores CSV
    assert "Dataclass,Complexity" in sections[2]
    assert "TOTAL," in sections[2]


def test_cli_csv_parseable(shared_datadir):
    """Test that CLI CSV output can be parsed."""
    import csv
    import io

    basic_file = shared_datadir / "basic.py"

    runner = CliRunner()
    result = runner.invoke(main, [str(basic_file)])

    assert result.exit_code == 0
    output = result.output

    # Extract first CSV section (complexity analysis)
    sections = output.split("-" * 80)
    complexity_section = sections[0].strip()

    # Parse as CSV
    reader = csv.DictReader(io.StringIO(complexity_section))
    rows = list(reader)

    # Should have multiple rows
    assert len(rows) > 0

    # Check that headers are correct
    first_row = rows[0]
    assert "Name" in first_row
    assert "Start" in first_row
    assert "End" in first_row
    assert "Total" in first_row


def test_cli_sections_order(shared_datadir):
    """Test that sections appear in correct order."""
    basic_file = shared_datadir / "basic.py"

    runner = CliRunner()
    result = runner.invoke(main, [str(basic_file)])

    assert result.exit_code == 0
    output = result.output

    # Find positions of key markers
    complexity_pos = output.find("Name,Start,End,Total")
    attribute_pos = output.find("Dataclass,Attribute,Type,Usage Count,Complexity")
    complexity_score_pos = output.find("Dataclass,Complexity")
    warning_pos = output.find("WARNING:")
    dataclasses_pos = output.find("Dataclasses:")
    routes_pos = output.find("Routes:")
    diagram_pos = output.find("classDiagram")
    graph_pos = output.find("graph TD")

    # Verify order: CSV sections first, then warnings/textual, then diagrams
    assert complexity_pos < attribute_pos < complexity_score_pos
    assert complexity_score_pos < warning_pos
    assert warning_pos < dataclasses_pos < routes_pos
    assert routes_pos < diagram_pos < graph_pos


def test_cli_all_data_present(shared_datadir):
    """Test that all expected data is present in CLI output."""
    basic_file = shared_datadir / "basic.py"

    runner = CliRunner()
    result = runner.invoke(main, [str(basic_file)])

    assert result.exit_code == 0
    output = result.output

    # Check for dataclass names
    assert "A" in output
    assert "B" in output
    assert "C" in output

    # Check for route names
    assert "first_page" in output
    assert "second_page" in output
    assert "third_page" in output
    assert "fourth_page" in output

    # Check for field names
    assert "field1" in output
    assert "field2" in output

    # Check for complexity scores
    assert "0.1" in output  # primitive complexity
    assert "1.0" in output  # list complexity
    assert "TOTAL" in output


def test_cli_complex_test_data(shared_datadir):
    """Test CLI with complex.py test data."""
    complex_file = shared_datadir / "complex.py"

    runner = CliRunner()
    result = runner.invoke(main, [str(complex_file)])

    assert result.exit_code == 0
    output = result.output

    # Should have State dataclass
    assert "State" in output
    assert "State,x,int" in output
    assert "State,y,str" in output

    # Should have unused warning
    assert "WARNING:" in output
    assert "State.y" in output


def test_cli_csv_file_output(shared_datadir, tmp_path):
    """Test that CSV file output works correctly."""
    basic_file = shared_datadir / "basic.py"
    csv_file = tmp_path / "test.csv"

    runner = CliRunner()
    result = runner.invoke(main, [str(basic_file), "--csv-file", str(csv_file)])

    assert result.exit_code == 0
    assert csv_file.exists()

    # Verify CSV content
    content = csv_file.read_text()
    assert "Name,Start,End,Total" in content
    assert "Dataclass,Attribute,Type,Usage Count,Complexity" in content
    assert "Dataclass,Complexity" in content
    assert "first_page" in content
    assert "A,field1,int" in content


def test_cli_mermaid_file_output(shared_datadir, tmp_path):
    """Test that Mermaid file output works correctly."""
    basic_file = shared_datadir / "basic.py"
    mermaid_file = tmp_path / "test.mmd"

    runner = CliRunner()
    result = runner.invoke(main, [str(basic_file), "--mermaid-file", str(mermaid_file)])

    assert result.exit_code == 0
    assert mermaid_file.exists()

    # Verify Mermaid content
    content = mermaid_file.read_text()
    assert "classDiagram" in content
    assert "graph TD" in content
    assert "class A {" in content
    assert "class B {" in content


def test_cli_html_file_output(shared_datadir, tmp_path):
    """Test that HTML file output works correctly."""
    basic_file = shared_datadir / "basic.py"
    html_file = tmp_path / "test.html"

    runner = CliRunner()
    result = runner.invoke(main, [str(basic_file), "--html-file", str(html_file)])

    assert result.exit_code == 0
    assert html_file.exists()

    # Verify HTML content
    content = html_file.read_text()
    assert "<!DOCTYPE html>" in content
    assert '<html lang="en">' in content
    assert "<title>Drafter Site Analysis</title>" in content
    assert "water.css" in content  # CSS framework
    assert "mermaid" in content  # Mermaid library
    assert "<table>" in content
    assert "<h2>Complexity Analysis</h2>" in content
    assert "<h2>Dataclass Attributes</h2>" in content
    assert "<h2>Class Diagram</h2>" in content
    assert "<h2>Function Call Graph</h2>" in content


def test_cli_no_stdout(shared_datadir, tmp_path):
    """Test that --no-stdout prevents output to stdout."""
    basic_file = shared_datadir / "basic.py"

    runner = CliRunner()
    result = runner.invoke(main, [str(basic_file), "--no-stdout"])

    assert result.exit_code == 0
    # Output should be empty or minimal
    assert "Name,Start,End,Total" not in result.output
    assert "classDiagram" not in result.output


def test_cli_disable_csv_output(shared_datadir, tmp_path):
    """Test that --no-csv prevents CSV file creation."""
    basic_file = shared_datadir / "basic.py"
    csv_file = tmp_path / "analysis.csv"

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [str(basic_file), "--no-csv"])

    assert result.exit_code == 0
    assert not csv_file.exists()


def test_cli_disable_mermaid_output(shared_datadir, tmp_path):
    """Test that --no-mermaid prevents Mermaid file creation."""
    basic_file = shared_datadir / "basic.py"
    mermaid_file = tmp_path / "analysis.mmd"

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [str(basic_file), "--no-mermaid"])

    assert result.exit_code == 0
    assert not mermaid_file.exists()


def test_cli_disable_html_output(shared_datadir, tmp_path):
    """Test that --no-html prevents HTML file creation."""
    basic_file = shared_datadir / "basic.py"
    html_file = tmp_path / "analysis.html"

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [str(basic_file), "--no-html"])

    assert result.exit_code == 0
    assert not html_file.exists()


def test_cli_custom_filenames(shared_datadir, tmp_path):
    """Test that custom filenames work for all output types."""
    basic_file = shared_datadir / "basic.py"
    csv_file = tmp_path / "custom.csv"
    mermaid_file = tmp_path / "custom.mmd"
    html_file = tmp_path / "custom.html"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(basic_file),
            "--csv-file",
            str(csv_file),
            "--mermaid-file",
            str(mermaid_file),
            "--html-file",
            str(html_file),
        ],
    )

    assert result.exit_code == 0
    assert csv_file.exists()
    assert mermaid_file.exists()
    assert html_file.exists()


def test_cli_default_files_created(shared_datadir, tmp_path):
    """Test that default filenames are used when not specified."""
    basic_file = shared_datadir / "basic.py"

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [str(basic_file)])

        assert result.exit_code == 0
        from pathlib import Path

        assert Path("analysis.csv").exists()
        assert Path("analysis.mmd").exists()
        assert Path("analysis.html").exists()
