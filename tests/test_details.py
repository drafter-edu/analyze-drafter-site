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


def test_route_button_links_with_leading_slash():
    """Test that Button links with leading slash in URLs are captured."""
    code = """
from drafter import *

@route
def index(state):
    return Page(state, [Button('Link', '/link')])

@route
def link(state):
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Check that leading slash URLs are tracked correctly
    assert "link" in analyzer.function_calls["index"]

    diagram = analyzer.generate_mermaid_function_diagram()
    assert "index --> link" in diagram


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

    # B: 1 custom (A) = 1, 1 list[A] (nested) = 10 => total=11
    complexity_b = analyzer._calculate_dataclass_complexity("B")
    assert complexity_b == 11.0


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


def test_csv_attribute_output():
    """Test that CSV attribute output is properly formatted."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class State:
    name: str
    age: int
    score: float

@route
def index(state: State):
    state.name = "Alice"
    state.age += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    csv_output = analyzer.get_dataclass_attribute_csv()

    # Check CSV header
    assert "Dataclass,Attribute,Type,Usage Count,Complexity" in csv_output

    # Check data rows are present
    assert "State,name,str,1,0.1" in csv_output
    assert "State,age,int,1,0.1" in csv_output
    assert "State,score,float,0,0.1" in csv_output

    # Verify it's comma-separated
    lines = csv_output.split("\n")
    assert len(lines) >= 4  # header + 3 data rows


def test_csv_complexity_output():
    """Test that CSV complexity output is properly formatted."""
    code = """
from dataclasses import dataclass

@dataclass
class Simple:
    x: int
    y: str

@dataclass
class Complex:
    items: list[int]
    data: dict[str, int]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    csv_output = analyzer.get_dataclass_complexity_csv()

    # Check CSV header
    assert "Dataclass,Complexity" in csv_output

    # Check data rows - Simple has 2 primitives (0.2)
    assert "Simple,0.2" in csv_output

    # Complex has 1 list (1) + 1 dict (10) = 11
    assert "Complex,11.0" in csv_output

    # Check TOTAL line
    assert "TOTAL,11.2" in csv_output

    # Verify format
    lines = csv_output.split("\n")
    for line in lines[1:]:  # Skip header
        if line:
            parts = line.split(",")
            assert len(parts) == 2


def test_csv_unused_warnings():
    """Test that unused warnings are properly formatted."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class Used:
    field1: int
    field2: str

@dataclass
class Unused:
    data: int

@route
def index(state: Used):
    state.field1 += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    warnings = analyzer.get_unused_warnings()

    # Check for unused dataclass warning
    assert (
        "WARNING: The following dataclasses are NOT used anywhere:" in warnings
    )
    assert "Unused" in warnings

    # Check for unused attribute warning
    assert (
        "WARNING: The following attributes are NOT used anywhere:" in warnings
    )
    assert "Used.field2" in warnings
    assert "Unused.data" in warnings


def test_csv_textual_details():
    """Test that textual details are properly formatted."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class State:
    count: int

@route
def index(state: State):
    return Page(state, [Button("Click", second)])

@route
def second(state: State):
    state.count += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    details = analyzer.get_textual_details()

    # Check dataclasses section
    assert "Dataclasses:" in details
    assert "State" in details
    assert "count" in details

    # Check routes section
    assert "Routes:" in details
    assert "index(state)" in details
    assert "second(state)" in details
    assert "Button: 1" in details
    assert "count used" in details


def test_csv_output_with_test_data(shared_datadir):
    """Test CSV output with basic.py test data."""
    with open(shared_datadir / "basic.py") as f:
        code = f.read()

    analyzer = Analyzer()
    analyzer.analyze(code)

    # Test attribute CSV
    attr_csv = analyzer.get_dataclass_attribute_csv()
    assert "Dataclass,Attribute,Type,Usage Count,Complexity" in attr_csv
    assert "A,field1,int" in attr_csv
    assert "A,field2,str" in attr_csv
    assert "B,a,A" in attr_csv
    assert "B,list_of_c,list[C]" in attr_csv

    # Test complexity CSV
    complexity_csv = analyzer.get_dataclass_complexity_csv()
    assert "Dataclass,Complexity" in complexity_csv
    assert "A,0.2" in complexity_csv
    assert "C,0.2" in complexity_csv
    assert "B,11.1" in complexity_csv
    assert "TOTAL,11.5" in complexity_csv

    # Test warnings
    warnings = analyzer.get_unused_warnings()
    assert "C.xxx" in warnings
    assert "C.yyy" in warnings
    assert "B.field3" in warnings
    assert "B.list_of_c" in warnings

    # Test textual details
    details = analyzer.get_textual_details()
    assert "Dataclasses:" in details
    assert "Routes:" in details
    assert "first_page" in details


def test_csv_output_parseable():
    """Test that CSV output can be parsed by csv module."""
    import csv
    import io

    code = """
from dataclasses import dataclass

@dataclass
class Test:
    x: int
    y: str
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Test attribute CSV is parseable
    attr_csv = analyzer.get_dataclass_attribute_csv()
    reader = csv.DictReader(io.StringIO(attr_csv))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["Dataclass"] == "Test"
    assert rows[0]["Attribute"] == "x"
    assert rows[0]["Type"] == "int"

    # Test complexity CSV is parseable
    complexity_csv = analyzer.get_dataclass_complexity_csv()
    reader = csv.DictReader(io.StringIO(complexity_csv))
    rows = list(reader)
    assert len(rows) == 2  # Test + TOTAL
    assert rows[0]["Dataclass"] == "Test"
    assert rows[1]["Dataclass"] == "TOTAL"


def test_csv_output_complex_types(shared_datadir):
    """Test CSV output with complex.py test data."""
    with open(shared_datadir / "complex.py") as f:
        code = f.read()

    analyzer = Analyzer()
    analyzer.analyze(code)

    # Test that State dataclass is detected
    attr_csv = analyzer.get_dataclass_attribute_csv()
    assert "State,x,int" in attr_csv
    assert "State,y,str" in attr_csv

    # Test complexity
    complexity_csv = analyzer.get_dataclass_complexity_csv()
    assert "State,0.2" in complexity_csv

    # Test warnings for unused attributes
    warnings = analyzer.get_unused_warnings()
    assert "State.y" in warnings


def test_csv_output_no_dataclasses():
    """Test CSV output when there are no dataclasses."""
    code = """
def helper():
    return 42
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    attr_csv = analyzer.get_dataclass_attribute_csv()
    assert "No dataclasses found" in attr_csv

    complexity_csv = analyzer.get_dataclass_complexity_csv()
    assert complexity_csv == ""

    warnings = analyzer.get_unused_warnings()
    assert warnings == ""

    details = analyzer.get_textual_details()
    assert details == ""


def test_csv_output_separation():
    """Test that CSV sections can be easily separated."""
    code = """
from dataclasses import dataclass

@dataclass
class A:
    x: int
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # Each method should produce independent output
    attr_csv = analyzer.get_dataclass_attribute_csv()
    complexity_csv = analyzer.get_dataclass_complexity_csv()
    warnings = analyzer.get_unused_warnings()
    details = analyzer.get_textual_details()

    # They should be separate strings
    assert isinstance(attr_csv, str)
    assert isinstance(complexity_csv, str)
    assert isinstance(warnings, str)
    assert isinstance(details, str)

    # No overlap between sections
    assert "Dataclass,Attribute" in attr_csv
    assert "Dataclass,Attribute" not in complexity_csv
    assert "Dataclass,Complexity" in complexity_csv
    assert "Dataclass,Complexity" not in attr_csv


def test_helper_function_calls_tracked():
    """Test that helper functions calling other helper functions are tracked."""
    code = """
from drafter import *

@route
def route1(state):
    result = helper1()
    return Page(state, [result])

def helper1():
    return helper2()

def helper2():
    return helper3()

def helper3():
    return "nested"
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # route1 should call helper1
    assert "helper1" in analyzer.function_calls["route1"]

    # helper1 should call helper2
    assert "helper2" in analyzer.function_calls["helper1"]

    # helper2 should call helper3
    assert "helper3" in analyzer.function_calls["helper2"]

    # Function diagram should show all connections
    diagram = analyzer.generate_mermaid_function_diagram()
    assert "route1 --> helper1" in diagram
    assert "helper1 --> helper2" in diagram
    assert "helper2 --> helper3" in diagram


def test_helper_function_with_multiple_calls():
    """Test that helper functions calling multiple other helpers are tracked."""
    code = """
from drafter import *

@route
def main_route(state):
    process_data()
    return Page(state, [])

def process_data():
    validate_input()
    transform_data()
    save_result()

def validate_input():
    pass

def transform_data():
    pass

def save_result():
    pass
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # main_route should call process_data
    assert "process_data" in analyzer.function_calls["main_route"]

    # process_data should call all three helpers
    process_calls = analyzer.function_calls["process_data"]
    assert "validate_input" in process_calls
    assert "transform_data" in process_calls
    assert "save_result" in process_calls

    # Function diagram should show all connections
    diagram = analyzer.generate_mermaid_function_diagram()
    assert "main_route --> process_data" in diagram
    assert "process_data --> validate_input" in diagram
    assert "process_data --> transform_data" in diagram
    assert "process_data --> save_result" in diagram


def test_todo_app_make_todo_list_tracked():
    """Test that make_todo_list is tracked in the call graph (issue regression test)."""
    code = """
from drafter import *

@dataclass
class TodoItem:
    id: int
    name: str
    completed: bool

@dataclass
class State:
    todos: list[TodoItem]

@route
def index(state: State) -> Page:
    current_items = make_todo_list(state.todos)
    return Page(state, [current_items])

def make_todo_toggle(completed: bool, target_id: int) -> Button:
    if completed:
        return Button("☑️", "toggle_complete", target_id)
    else:
        return Button("🔲", "toggle_complete", target_id)

def make_todo_list(todos: list[TodoItem]) -> PageContent:
    if not todos:
        return Div("No items yet.")
    items = []
    for todo in todos:
        items.append([
            make_todo_toggle(todo.completed, todo.id),
            Div(todo.name),
        ])
    return Table(items)

@route
def toggle_complete(state: State, target_id: int) -> Page:
    return index(state)
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # index should call make_todo_list
    assert "make_todo_list" in analyzer.function_calls["index"]

    # make_todo_list should call make_todo_toggle (this was the bug)
    assert "make_todo_toggle" in analyzer.function_calls["make_todo_list"]

    # make_todo_toggle should link to toggle_complete route via Button
    assert "toggle_complete" in analyzer.function_calls["make_todo_toggle"]

    # Function diagram should show the connection
    diagram = analyzer.generate_mermaid_function_diagram()
    assert "index --> make_todo_list" in diagram
    assert "make_todo_list --> make_todo_toggle" in diagram
    assert "make_todo_toggle --> toggle_complete" in diagram


def test_helper_function_button_links_to_routes():
    """Test that Button links in helper functions to routes are captured (GitHub issue)."""
    code = """
from drafter import *

@dataclass
class TodoItem:
    id: int
    name: str

@dataclass
class State:
    todos: list[TodoItem]

@route
def index(state: State) -> Page:
    current_items = make_todo_list(state.todos)
    return Page(state, [current_items])

def make_todo_list(todos: list[TodoItem]) -> PageContent:
    if not todos:
        return Div("No items yet.")
    items = []
    for todo in todos:
        items.append([
            Button("Remove", "remove_todo", todo.id),
            Button("Edit", "edit_todo", todo.id),
        ])
    return Table(items)

@route
def remove_todo(state: State, target_id: int) -> Page:
    return index(state)

@route
def edit_todo(state: State, target_id: int) -> Page:
    return index(state)
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # make_todo_list should link to remove_todo and edit_todo routes via Buttons
    assert "remove_todo" in analyzer.function_calls["make_todo_list"]
    assert "edit_todo" in analyzer.function_calls["make_todo_list"]

    # Function diagram should show all connections
    diagram = analyzer.generate_mermaid_function_diagram()
    assert "make_todo_list --> remove_todo" in diagram
    assert "make_todo_list --> edit_todo" in diagram


def test_nested_field_complexity_list_of_primitives():
    """Test that list[int] remains score 1 (not nested)."""
    code = """
from dataclasses import dataclass

@dataclass
class Test:
    field: list[int]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    complexity = analyzer._calculate_dataclass_complexity("Test")
    assert complexity == 1.0


def test_nested_field_complexity_list_of_list():
    """Test that list[list[int]] is scored as 10 (nested)."""
    code = """
from dataclasses import dataclass

@dataclass
class Test:
    field: list[list[int]]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    complexity = analyzer._calculate_dataclass_complexity("Test")
    assert complexity == 10.0


def test_nested_field_complexity_list_of_dataclass():
    """Test that list[Dataclass] is scored as 10 (nested)."""
    code = """
from dataclasses import dataclass

@dataclass
class Tile:
    value: int

@dataclass
class Test:
    field: list[Tile]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    complexity = analyzer._calculate_dataclass_complexity("Test")
    assert complexity == 10.0


def test_nested_field_complexity_plain_dataclass():
    """Test that plain Dataclass field remains score 1."""
    code = """
from dataclasses import dataclass

@dataclass
class Tile:
    value: int

@dataclass
class Test:
    field: Tile
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    complexity = analyzer._calculate_dataclass_complexity("Test")
    assert complexity == 1.0


def test_nested_field_complexity_triple_nested():
    """Test that list[list[list[int]]] is scored as 10 (doesn't stack)."""
    code = """
from dataclasses import dataclass

@dataclass
class Test:
    field: list[list[list[int]]]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    complexity = analyzer._calculate_dataclass_complexity("Test")
    assert complexity == 10.0


def test_nested_field_complexity_dict_with_dataclass():
    """Test that dict[str, Dataclass] remains score 10."""
    code = """
from dataclasses import dataclass

@dataclass
class Tile:
    value: int

@dataclass
class Test:
    field: dict[str, Tile]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    complexity = analyzer._calculate_dataclass_complexity("Test")
    assert complexity == 10.0


def test_nested_field_complexity_mixed_fields():
    """Test complexity with mixed nested and non-nested fields."""
    code = """
from dataclasses import dataclass

@dataclass
class Item:
    name: str

@dataclass
class Test:
    simple_int: int
    simple_list: list[int]
    nested_list: list[list[int]]
    dataclass_list: list[Item]
    plain_dataclass: Item
    simple_dict: dict[str, int]
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    # simple_int: 0.1
    # simple_list: 1
    # nested_list: 10
    # dataclass_list: 10
    # plain_dataclass: 1
    # simple_dict: 10
    # Total: 0.1 + 1 + 10 + 10 + 1 + 10 = 32.1
    complexity = analyzer._calculate_dataclass_complexity("Test")
    assert complexity == 32.1


def test_unused_fields_csv_basic():
    """Test that unused fields CSV is properly formatted."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class State:
    used_field: int
    unused_field: str
    another_unused: bool

@route
def index(state: State):
    state.used_field += 1
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    csv_output = analyzer.get_unused_fields_csv()

    # Check CSV header
    assert "Dataclass,Attribute" in csv_output

    # Check unused fields are present
    assert "State,unused_field" in csv_output
    assert "State,another_unused" in csv_output

    # Check used field is NOT present
    assert "State,used_field" not in csv_output or "used_field" not in csv_output.split("\n")[1:]


def test_unused_fields_csv_no_unused():
    """Test that unused fields CSV returns empty string when all fields are used."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class State:
    x: int
    y: str

@route
def index(state: State):
    state.x += 1
    state.y = "hello"
    return Page(state, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    csv_output = analyzer.get_unused_fields_csv()

    # Should return empty string when no unused fields
    assert csv_output == ""


def test_unused_fields_csv_multiple_classes():
    """Test unused fields CSV with multiple dataclasses."""
    code = """
from dataclasses import dataclass
from drafter import *

@dataclass
class A:
    used: int
    unused: str

@dataclass
class B:
    all_unused: bool
    also_unused: float

@dataclass
class C:
    all_used: int

@route
def index(a: A, c: C):
    a.used += 1
    c.all_used = 5
    return Page(a, [])
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    csv_output = analyzer.get_unused_fields_csv()

    # Check header
    assert "Dataclass,Attribute" in csv_output

    # Check unused fields from A
    assert "A,unused" in csv_output

    # Check unused fields from B (completely unused class)
    assert "B,all_unused" in csv_output
    assert "B,also_unused" in csv_output

    # Check C has no unused fields in the output
    lines = csv_output.split("\n")
    c_lines = [line for line in lines if line.startswith("C,")]
    assert len(c_lines) == 0


def test_unused_fields_csv_no_dataclasses():
    """Test that unused fields CSV returns empty string when there are no dataclasses."""
    code = """
def helper():
    return 42
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    csv_output = analyzer.get_unused_fields_csv()
    assert csv_output == ""


def test_unused_fields_csv_parseable():
    """Test that unused fields CSV can be parsed by csv module."""
    import csv
    import io

    code = """
from dataclasses import dataclass

@dataclass
class Test:
    unused1: int
    unused2: str
"""
    analyzer = Analyzer()
    analyzer.analyze(code)

    csv_output = analyzer.get_unused_fields_csv()
    reader = csv.DictReader(io.StringIO(csv_output))
    rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["Dataclass"] == "Test"
    assert rows[0]["Attribute"] == "unused1"
    assert rows[1]["Dataclass"] == "Test"
    assert rows[1]["Attribute"] == "unused2"
