"""Tests for mypy integration in dataclass attribute tracking."""

from analyze_drafter_site import Analyzer


def test_mypy_disambiguates_same_field_names():
    """Test that mypy correctly distinguishes between dataclasses with same field names.
    
    This is the main improvement over the old AST-only approach.
    """
    code = """
from drafter import *
from dataclasses import dataclass

@dataclass
class StateA:
    count: int
    name: str

@dataclass
class StateB:
    count: int
    age: int

@route
def page_a(state: StateA):
    state.count += 1
    return Page(state, [])

@route
def page_b(state: StateB):
    state.age += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # StateA.count should be used exactly once
    assert analyzer.attribute_usage["StateA"]["count"] == 1
    # StateA.name should not be used
    assert analyzer.attribute_usage["StateA"]["name"] == 0
    
    # StateB.count should NOT be counted (never accessed)
    assert analyzer.attribute_usage["StateB"]["count"] == 0
    # StateB.age should be used exactly once
    assert analyzer.attribute_usage["StateB"]["age"] == 1


def test_mypy_nested_attribute_access():
    """Test that mypy helps with nested attribute access like b.a.field."""
    code = """
from drafter import *
from dataclasses import dataclass

@dataclass
class A:
    field1: int
    field2: str

@dataclass
class B:
    a: A
    name: str

@route
def page(b: B):
    b.a.field1 += 1
    return Page(b, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # B.a should be accessed
    assert analyzer.attribute_usage["B"]["a"] >= 1
    # A.field1 should be accessed
    assert analyzer.attribute_usage["A"]["field1"] >= 1
    # A.field2 should not be accessed
    assert analyzer.attribute_usage["A"]["field2"] == 0
    # B.name should not be accessed
    assert analyzer.attribute_usage["B"]["name"] == 0


def test_mypy_fallback_when_type_unknown():
    """Test that the system falls back to old behavior when type is unknown.
    
    This ensures backwards compatibility when mypy can't determine the type.
    """
    code = """
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    count: int

def helper():
    # No type annotation - mypy can't help here
    obj = get_something()
    obj.count += 1

@route
def page(state: State):
    state.count += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # State.count should still be tracked
    # It will be counted at least once from the route
    assert analyzer.attribute_usage["State"]["count"] >= 1


def test_mypy_with_multiple_parameters():
    """Test mypy tracking with multiple function parameters."""
    code = """
from drafter import *
from dataclasses import dataclass

@dataclass
class StateA:
    x: int

@dataclass
class StateB:
    y: int

@route
def page(state_a: StateA, state_b: StateB):
    state_a.x += 1
    state_b.y += 1
    return Page(state_a, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # Each state's field should be tracked independently
    assert analyzer.attribute_usage["StateA"]["x"] == 1
    assert analyzer.attribute_usage["StateB"]["y"] == 1


def test_mypy_variable_types_extracted():
    """Test that mypy correctly extracts variable types."""
    code = """
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    count: int

@route
def page_a(state: State):
    return Page(state, [])

@route
def page_b(data: State):
    return Page(data, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # Check that variable types were extracted
    assert "page_a.state" in analyzer.variable_types
    assert analyzer.variable_types["page_a.state"] == "State"
    assert "page_b.data" in analyzer.variable_types
    assert analyzer.variable_types["page_b.data"] == "State"


def test_mypy_ignores_non_dataclass_types():
    """Test that mypy only tracks dataclass types, not built-in types."""
    code = """
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    count: int

@route
def page(state: State, name: str, value: int):
    state.count += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # Only State should be tracked
    assert "page.state" in analyzer.variable_types
    assert analyzer.variable_types["page.state"] == "State"
    # Built-in types should not be in variable_types
    assert "page.name" not in analyzer.variable_types
    assert "page.value" not in analyzer.variable_types


def test_mypy_with_union_types():
    """Test mypy handling of union types (Optional, etc.)."""
    code = """
from drafter import *
from dataclasses import dataclass
from typing import Optional

@dataclass
class State:
    count: int

@route
def page(state: Optional[State]):
    if state:
        state.count += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # Mypy should still extract State from Optional[State]
    assert "page.state" in analyzer.variable_types
    assert analyzer.variable_types["page.state"] == "State"
