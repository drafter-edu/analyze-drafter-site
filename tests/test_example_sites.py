import pytest
from analyze_drafter_site import Analyzer


def test_basic_site(shared_datadir):
    with open(shared_datadir / "basic.py") as f:
        code = f.read()
    analyzer = Analyzer()
    analyzer.analyze(code)
    for result in analyzer.save_as_string():
        print(result)
    
    assert len(analyzer.dataclasses) == 3
    assert len(analyzer.routes) == 4
