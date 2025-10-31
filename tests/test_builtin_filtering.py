"""Tests for filtering built-in functions from call graph."""

from analyze_drafter_site import Analyzer


def test_builtin_functions_excluded_from_call_graph():
    """Test that built-in functions are not included in the call graph."""
    code = """
from drafter import *

@route
def index(state):
    # Built-in functions that should be excluded
    name = str(42)
    length = len([1, 2, 3])
    total = sum([1, 2, 3])
    number = int("42")
    value = float("3.14")
    text = repr(name)
    is_true = bool(1)
    items = list(range(5))
    unique = set([1, 2, 3])
    pairs = dict(a=1, b=2)
    maximum = max([1, 2, 3])
    minimum = min([1, 2, 3])
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check that built-in functions are NOT in the call graph
    if "index" in analyzer.function_calls:
        calls = analyzer.function_calls["index"]

        # These built-in functions should NOT be tracked
        assert "str" not in calls
        assert "len" not in calls
        assert "sum" not in calls
        assert "int" not in calls
        assert "float" not in calls
        assert "repr" not in calls
        assert "bool" not in calls
        assert "list" not in calls
        assert "set" not in calls
        assert "dict" not in calls
        assert "max" not in calls
        assert "min" not in calls
        assert "range" not in calls

        # Page is a component, already filtered separately
        assert "Page" not in calls


def test_user_defined_functions_included_in_call_graph():
    """Test that user-defined functions ARE included in the call graph."""
    code = """
from drafter import *

def helper():
    return "data"

def another_helper():
    return 42

@route
def index(state):
    data = helper()
    value = another_helper()
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check that user-defined functions ARE in the call graph
    assert "index" in analyzer.function_calls
    calls = analyzer.function_calls["index"]
    assert "helper" in calls
    assert "another_helper" in calls


def test_mixed_builtin_and_user_functions():
    """Test that only user-defined functions are tracked, not built-ins."""
    code = """
from drafter import *

def my_function():
    return "custom"

@route
def index(state):
    # User-defined function - should be tracked
    result = my_function()

    # Built-in functions - should NOT be tracked
    name = str(result)
    length = len(name)

    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    assert "index" in analyzer.function_calls
    calls = analyzer.function_calls["index"]

    # User-defined function should be tracked
    assert "my_function" in calls

    # Built-in functions should NOT be tracked
    assert "str" not in calls
    assert "len" not in calls


def test_function_diagram_excludes_builtins():
    """Test that the mermaid function diagram excludes built-in functions."""
    code = """
from drafter import *

def helper():
    return "data"

@route
def index(state):
    data = helper()
    name = str(data)  # Built-in
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    diagram = analyzer.generate_mermaid_function_diagram()

    # User-defined function should be in the diagram
    assert "index --> helper" in diagram

    # Built-in function should NOT be in the diagram
    assert "str" not in diagram


def test_method_calls_not_tracked():
    """Test that method calls like .append() are not tracked as function calls."""
    code = """
from drafter import *

@route
def index(state):
    items = [1, 2, 3]
    items.append(4)  # Method call, not a function call
    items.extend([5, 6])
    name = "hello"
    name.upper()
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Methods should not appear in the function call graph
    if "index" in analyzer.function_calls:
        calls = analyzer.function_calls["index"]
        # These method names should NOT be tracked
        assert "append" not in calls
        assert "extend" not in calls
        assert "upper" not in calls


def test_empty_call_graph_with_only_builtins():
    """Test that routes using only built-ins have empty call graphs."""
    code = """
from drafter import *

@route
def index(state):
    # Only using built-ins and components
    name = str(42)
    length = len([1, 2, 3])
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # The call graph should be empty or not contain built-ins
    if "index" in analyzer.function_calls:
        calls = analyzer.function_calls["index"]
        # Should not contain any built-in functions
        assert "str" not in calls
        assert "len" not in calls
        # Page is a component, filtered separately
        assert "Page" not in calls
