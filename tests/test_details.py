"""Tests for the details module functionality."""

from analyze_drafter_site import Analyzer


def test_class_diagram_field_types():
    """Test that class diagrams show proper type names, not AST dumps."""
    code = """
from dataclasses import dataclass

@dataclass
class State:
    username: str
    count: int
    active: bool
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    diagram = analyzer.generate_mermaid_class_diagram()

    # Should contain readable type names
    assert "str username" in diagram
    assert "int count" in diagram
    assert "bool active" in diagram

    # Should NOT contain AST dumps
    assert "Name(id=" not in diagram
    assert "ctx=Load()" not in diagram


def test_class_composition_relationships():
    """Test that composition relationships between dataclasses are detected."""
    code = """
from dataclasses import dataclass

@dataclass
class A:
    field1: int

@dataclass
class B:
    a: A
    field2: str
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check that dependencies are detected
    assert "a" in analyzer.dataclasses["B"].fields
    assert "A" in analyzer.dataclasses["B"].dependencies

    diagram = analyzer.generate_mermaid_class_diagram()
    assert "B --> A" in diagram


def test_class_list_composition():
    """Test that list[Type] composition relationships are detected."""
    code = """
from dataclasses import dataclass

@dataclass
class Item:
    name: str

@dataclass
class Container:
    items: list[Item]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check that list type is properly handled
    assert "Item" in analyzer.dataclasses["Container"].dependencies

    diagram = analyzer.generate_mermaid_class_diagram()
    assert "list[Item] items" in diagram
    assert "Container --> Item" in diagram


def test_route_button_links():
    """Test that Button links to other routes are captured."""
    code = """
from drafter import *

@route
def first_page(state):
    return Page(state, [Button('Next', second_page)])

@route
def second_page(state):
    return Page(state, [Button('Back', first_page)])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check function calls are tracked
    assert "second_page" in analyzer.function_calls["first_page"]
    assert "first_page" in analyzer.function_calls["second_page"]

    diagram = analyzer.generate_mermaid_function_diagram()
    assert "first_page --> second_page" in diagram
    assert "second_page --> first_page" in diagram


def test_route_string_button_links():
    """Test that Button links with string names are captured."""
    code = """
from drafter import *

@route
def index(state):
    return Page(state, [Button('Go', 'target_page')])

@route
def target_page(state):
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check string references are tracked
    assert "target_page" in analyzer.function_calls["index"]


def test_route_direct_calls():
    """Test that direct route function calls are captured."""
    code = """
from drafter import *

@route
def first(state):
    return second(state)

@route
def second(state):
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check direct calls are tracked
    assert "second" in analyzer.function_calls["first"]

    diagram = analyzer.generate_mermaid_function_diagram()
    assert "first --> second" in diagram


def test_route_helper_function_calls():
    """Test that calls to non-route helper functions are captured."""
    code = """
from drafter import *

def helper():
    return "data"

@route
def index(state):
    data = helper()
    return Page(state, [data])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check helper function calls are tracked
    assert "helper" in analyzer.function_calls["index"]

    diagram = analyzer.generate_mermaid_function_diagram()
    assert "index --> helper" in diagram


def test_link_component():
    """Test that Link component references are captured."""
    code = """
from drafter import *

@route
def index(state):
    return Page(state, [Link('Click', 'target')])

@route
def target(state):
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check Link references are tracked
    assert "target" in analyzer.function_calls["index"]


def test_complex_route_graph(shared_datadir):
    """Test the complex route graph from basic.py."""
    with open(shared_datadir / "basic.py") as f:
        code = f.read()

    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check dataclasses are detected
    assert "A" in analyzer.dataclasses
    assert "B" in analyzer.dataclasses
    assert "C" in analyzer.dataclasses

    # Check composition relationships
    assert "A" in analyzer.dataclasses["B"].dependencies
    assert "C" in analyzer.dataclasses["B"].dependencies

    # Check routes are detected
    route_names = [r.name for r in analyzer.routes]
    assert "first_page" in route_names
    assert "second_page" in route_names
    assert "third_page" in route_names
    assert "fourth_page" in route_names

    # Check function calls are tracked
    assert "second_page" in analyzer.function_calls["first_page"]
    assert "fourth_page" in analyzer.function_calls["first_page"]
    assert "another_func" in analyzer.function_calls["first_page"]
    assert "third_page" in analyzer.function_calls["fourth_page"]

    # Verify diagrams are generated correctly
    class_diagram = analyzer.generate_mermaid_class_diagram()
    assert "B --> A" in class_diagram
    assert "B --> C" in class_diagram
    assert "int field1" in class_diagram
    assert "str field2" in class_diagram

    function_diagram = analyzer.generate_mermaid_function_diagram()
    assert "first_page --> second_page" in function_diagram
    assert "first_page --> fourth_page" in function_diagram
    assert "fourth_page --> third_page" in function_diagram


def test_decorator_with_arguments():
    """Test that @route with arguments is handled correctly."""
    code = """
from drafter import *

@route("/path")
def index(state):
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check route is detected even with decorator arguments
    assert len(analyzer.routes) == 1
    assert analyzer.routes[0].name == "index"


def test_attribute_usage_tracking():
    """Test that attribute usage is tracked correctly."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class State:
    x: int
    y: str
    z: bool

@route
def index(state: State):
    state.x += 1
    state.y = "hello"
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # Check that usage is tracked
    assert analyzer.attribute_usage["State"]["x"] == 1
    assert analyzer.attribute_usage["State"]["y"] == 1
    assert analyzer.attribute_usage["State"]["z"] == 0


def test_complexity_calculation_primitives():
    """Test complexity calculation for primitive types."""
    code = """
from dataclasses import dataclass

@dataclass
class Simple:
    a: int
    b: str
    c: bool
    d: float
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # Each primitive should be 0.1
    complexity = analyzer._calculate_dataclass_complexity("Simple")
    assert complexity == 0.4


def test_complexity_calculation_collections():
    """Test complexity calculation for collection types."""
    code = """
from dataclasses import dataclass

@dataclass
class Collections:
    a_list: list[int]
    a_dict: dict[str, int]
    a_tuple: tuple[int, str]
    a_set: set[str]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # list=1, dict=10, tuple=10, set=10 => total=31
    complexity = analyzer._calculate_dataclass_complexity("Collections")
    assert complexity == 31.0


def test_complexity_calculation_custom_types():
    """Test complexity calculation for custom dataclass types."""
    code = """
from dataclasses import dataclass

@dataclass
class A:
    value: int

@dataclass
class B:
    a: A
    items: list[A]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # A: 1 int = 0.1
    complexity_a = analyzer._calculate_dataclass_complexity("A")
    assert complexity_a == 0.1
    
    # B: 1 custom (A) = 1, 1 list = 1 => total=2
    complexity_b = analyzer._calculate_dataclass_complexity("B")
    assert complexity_b == 2.0


def test_unused_dataclass_detection():
    """Test detection of unused dataclasses."""
    code = """
from dataclasses import dataclass

@dataclass
class Used:
    value: int

@dataclass
class Unused:
    value: int

@dataclass
class Container:
    used: Used
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    analysis = analyzer.generate_dataclass_analysis()
    
    # Unused should not be flagged since checking dependencies
    # Container uses Used, so Used is not unused
    # Unused has no usage
    assert "Unused" not in analysis or "NOT used" in analysis


def test_unused_attributes_detection():
    """Test detection of unused attributes."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class State:
    used_field: int
    unused_field: str

@route
def index(state: State):
    state.used_field += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    analysis = analyzer.generate_dataclass_analysis()
    
    # Check that unused_field is flagged
    assert "State.unused_field" in analysis
    assert "NOT used" in analysis


def test_dataclass_analysis_table_format():
    """Test that dataclass analysis produces a table."""
    code = """
from dataclasses import dataclass

@dataclass
class Test:
    field1: int
    field2: str
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    analysis = analyzer.generate_dataclass_analysis()
    
    # Check that it contains table headers
    assert "Dataclass" in analysis
    assert "Attribute" in analysis
    assert "Type" in analysis
    assert "Usage Count" in analysis
    assert "Complexity" in analysis
    
    # Check it contains the data
    assert "Test" in analysis
    assert "field1" in analysis
    assert "field2" in analysis


def test_nested_attribute_access():
    """Test tracking of nested attribute access like b.a.field1."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class A:
    field1: int

@dataclass
class B:
    a: A

@route
def index(b: B):
    b.a.field1 += 1
    return Page(b, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)
    
    # Both 'a' and 'field1' should be tracked
    assert analyzer.attribute_usage["B"]["a"] >= 1
    assert analyzer.attribute_usage["A"]["field1"] >= 1

