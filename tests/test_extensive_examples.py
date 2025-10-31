"""Extensive tests for ghost_hunt.py, commenter.py, protein_lookup.py, and todo.py examples."""

import pytest
from analyze_drafter_site import Analyzer


class TestGhostHunt:
    """Comprehensive tests for ghost_hunt.py example."""

    def test_ghost_hunt_dataclasses(self, shared_datadir):
        """Test that all dataclasses in ghost_hunt.py are detected."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # Check dataclasses are detected
        assert "Tile" in analyzer.dataclasses
        assert "State" in analyzer.dataclasses
        assert len(analyzer.dataclasses) == 2

    def test_ghost_hunt_tile_fields(self, shared_datadir):
        """Test that Tile dataclass fields are correctly detected."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        tile_fields = analyzer.dataclasses["Tile"].fields
        assert "text" in tile_fields
        assert "flipped" in tile_fields
        assert "x" in tile_fields
        assert "y" in tile_fields
        assert len(tile_fields) == 4

    def test_ghost_hunt_state_fields(self, shared_datadir):
        """Test that State dataclass fields are correctly detected."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        state_fields = analyzer.dataclasses["State"].fields
        assert "grid" in state_fields
        assert "seed" in state_fields
        assert "score" in state_fields
        assert "size" in state_fields
        assert "ghosts" in state_fields
        assert len(state_fields) == 5

    def test_ghost_hunt_routes(self, shared_datadir):
        """Test that all routes in ghost_hunt.py are detected."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        route_names = [r.name for r in analyzer.routes]
        assert "index" in route_names
        assert "new_game" in route_names
        assert "play_game" in route_names
        assert "flip_tile" in route_names
        assert "game_won" in route_names
        assert len(route_names) == 5

    def test_ghost_hunt_helper_functions(self, shared_datadir):
        """Test that helper functions are tracked."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # Check that some key helper functions are tracked in function calls
        # new_game should call make_ghost_grid and play_game
        assert "make_ghost_grid" in analyzer.function_calls.get("new_game", [])
        assert "play_game" in analyzer.function_calls.get("new_game", [])

    def test_ghost_hunt_route_flow(self, shared_datadir):
        """Test that route flow is correctly captured."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # index should call new_game (via Button)
        assert "new_game" in analyzer.function_calls.get("index", [])
        
        # new_game should call play_game
        assert "play_game" in analyzer.function_calls.get("new_game", [])
        
        # flip_tile should call either play_game or game_won
        flip_tile_calls = analyzer.function_calls.get("flip_tile", [])
        assert "play_game" in flip_tile_calls or "game_won" in flip_tile_calls

    def test_ghost_hunt_attribute_usage(self, shared_datadir):
        """Test that State attributes are tracked for usage."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # State attributes should be used in routes
        assert "State" in analyzer.attribute_usage
        state_usage = analyzer.attribute_usage["State"]
        
        # grid, score, and ghosts should be used
        assert state_usage.get("grid", 0) > 0
        assert state_usage.get("score", 0) > 0
        assert state_usage.get("ghosts", 0) > 0

    def test_ghost_hunt_complexity(self, shared_datadir):
        """Test complexity calculation for ghost_hunt.py."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # State has complex list[list[Tile]] field
        state_complexity = analyzer._calculate_dataclass_complexity("State")
        # grid: list[list[Tile]] (1 for list), seed: int (0.1), score: int (0.1), 
        # size: int (0.1), ghosts: int (0.1)
        # Total should be > 1
        assert state_complexity > 1

    def test_ghost_hunt_mermaid_class_diagram(self, shared_datadir):
        """Test that class diagram shows relationships.
        
        Note: This test currently fails because the analyzer doesn't detect
        nested subscripts like list[list[Tile]] as dependencies. This is a
        known limitation and the test correctly identifies this gap.
        """
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        diagram = analyzer.generate_mermaid_class_diagram()
        
        # Should contain both classes
        assert "class Tile" in diagram
        assert "class State" in diagram
        
        # State should have dependency on Tile (via grid: list[list[Tile]])
        # This currently fails due to nested list not being parsed for dependencies
        # The test is correct - it exposes a limitation in the analyzer
        assert "Tile" in analyzer.dataclasses["State"].dependencies

    def test_ghost_hunt_mermaid_function_diagram(self, shared_datadir):
        """Test that function diagram shows route relationships."""
        with open(shared_datadir / "ghost_hunt.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        diagram = analyzer.generate_mermaid_function_diagram()
        
        # Should contain route nodes
        assert "index" in diagram
        assert "new_game" in diagram
        assert "play_game" in diagram
        
        # Should show relationships
        assert "index --> new_game" in diagram or "new_game" in analyzer.function_calls.get("index", [])


class TestCommenter:
    """Comprehensive tests for commenter.py example."""

    def test_commenter_dataclasses(self, shared_datadir):
        """Test that all dataclasses in commenter.py are detected."""
        with open(shared_datadir / "commenter.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # Check dataclasses are detected
        assert "Line" in analyzer.dataclasses
        assert "State" in analyzer.dataclasses
        assert len(analyzer.dataclasses) == 2

    def test_commenter_line_fields(self, shared_datadir):
        """Test that Line dataclass fields are correctly detected."""
        with open(shared_datadir / "commenter.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        line_fields = analyzer.dataclasses["Line"].fields
        assert "original" in line_fields
        assert "comment" in line_fields
        assert "index" in line_fields
        assert len(line_fields) == 3

    def test_commenter_state_fields(self, shared_datadir):
        """Test that State dataclass fields are correctly detected."""
        with open(shared_datadir / "commenter.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        state_fields = analyzer.dataclasses["State"].fields
        assert "comments" in state_fields
        assert "original_text" in state_fields
        assert len(state_fields) == 2

    def test_commenter_routes(self, shared_datadir):
        """Test that all routes in commenter.py are detected."""
        with open(shared_datadir / "commenter.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        route_names = [r.name for r in analyzer.routes]
        assert "index" in route_names
        assert "error_page" in route_names
        assert "start_commenting" in route_names
        assert "page_commenter" in route_names
        assert "comment" in route_names
        assert "save_comment" in route_names
        assert len(route_names) == 6

    def test_commenter_helper_functions(self, shared_datadir):
        """Test that helper functions are tracked."""
        with open(shared_datadir / "commenter.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # parse_lines should be called from start_commenting
        assert "parse_lines" in analyzer.function_calls.get("start_commenting", [])

    def test_commenter_route_flow(self, shared_datadir):
        """Test that route flow is correctly captured."""
        with open(shared_datadir / "commenter.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # start_commenting should call page_commenter or error_page
        start_calls = analyzer.function_calls.get("start_commenting", [])
        assert "page_commenter" in start_calls or "error_page" in start_calls
        
        # comment should be accessible from page_commenter (via Button)
        page_calls = analyzer.function_calls.get("page_commenter", [])
        assert "comment" in page_calls
        
        # save_comment should call page_commenter
        assert "page_commenter" in analyzer.function_calls.get("save_comment", [])

    def test_commenter_attribute_usage(self, shared_datadir):
        """Test that attributes are tracked for usage."""
        with open(shared_datadir / "commenter.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # State attributes should be used
        assert "State" in analyzer.attribute_usage
        state_usage = analyzer.attribute_usage["State"]
        assert state_usage.get("comments", 0) > 0

    def test_commenter_complexity(self, shared_datadir):
        """Test complexity calculation for commenter.py."""
        with open(shared_datadir / "commenter.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # State has list[Line] which should contribute to complexity
        state_complexity = analyzer._calculate_dataclass_complexity("State")
        assert state_complexity > 1  # list adds 1, plus primitives


class TestProteinLookup:
    """Comprehensive tests for protein_lookup.py example."""

    def test_protein_lookup_dataclasses(self, shared_datadir):
        """Test that all dataclasses in protein_lookup.py are detected."""
        with open(shared_datadir / "protein_lookup.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # Check dataclasses are detected
        assert "State" in analyzer.dataclasses
        assert "Food" in analyzer.dataclasses
        assert len(analyzer.dataclasses) == 2

    def test_protein_lookup_food_fields(self, shared_datadir):
        """Test that Food dataclass fields are correctly detected."""
        with open(shared_datadir / "protein_lookup.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        food_fields = analyzer.dataclasses["Food"].fields
        assert "category" in food_fields
        assert "name" in food_fields
        assert "id" in food_fields
        assert "protein" in food_fields
        assert len(food_fields) == 4

    def test_protein_lookup_state_fields(self, shared_datadir):
        """Test that State dataclass fields are correctly detected."""
        with open(shared_datadir / "protein_lookup.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        state_fields = analyzer.dataclasses["State"].fields
        assert "food_items" in state_fields
        assert len(state_fields) == 1

    def test_protein_lookup_routes(self, shared_datadir):
        """Test that all routes in protein_lookup.py are detected."""
        with open(shared_datadir / "protein_lookup.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        route_names = [r.name for r in analyzer.routes]
        assert "index" in route_names
        assert "search" in route_names
        assert "add_food" in route_names
        assert len(route_names) == 3

    def test_protein_lookup_helper_functions(self, shared_datadir):
        """Test that helper functions are tracked."""
        with open(shared_datadir / "protein_lookup.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # index should call get_food and total_protein
        index_calls = analyzer.function_calls.get("index", [])
        assert "get_food" in index_calls
        assert "total_protein" in index_calls
        
        # search should call find_foods
        search_calls = analyzer.function_calls.get("search", [])
        assert "find_foods" in search_calls
        assert "no_food_found_page" in search_calls or "make_food_button" in search_calls

    def test_protein_lookup_route_flow(self, shared_datadir):
        """Test that route flow is correctly captured."""
        with open(shared_datadir / "protein_lookup.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # index should have Button to search
        assert "search" in analyzer.function_calls.get("index", [])
        
        # add_food should call index
        assert "index" in analyzer.function_calls.get("add_food", [])

    def test_protein_lookup_attribute_usage(self, shared_datadir):
        """Test that attributes are tracked for usage."""
        with open(shared_datadir / "protein_lookup.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # State.food_items should be used
        assert "State" in analyzer.attribute_usage
        state_usage = analyzer.attribute_usage["State"]
        assert state_usage.get("food_items", 0) > 0

    def test_protein_lookup_complexity(self, shared_datadir):
        """Test complexity calculation for protein_lookup.py."""
        with open(shared_datadir / "protein_lookup.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # Food has 4 primitive fields
        food_complexity = analyzer._calculate_dataclass_complexity("Food")
        assert food_complexity == 0.4  # 4 primitives * 0.1

        # State has list[int]
        state_complexity = analyzer._calculate_dataclass_complexity("State")
        assert state_complexity == 1.0  # list adds 1


class TestTodo:
    """Comprehensive tests for todo.py example."""

    def test_todo_dataclasses(self, shared_datadir):
        """Test that all dataclasses in todo.py are detected."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # Check dataclasses are detected
        assert "TodoItem" in analyzer.dataclasses
        assert "State" in analyzer.dataclasses
        assert len(analyzer.dataclasses) == 2

    def test_todo_todoitem_fields(self, shared_datadir):
        """Test that TodoItem dataclass fields are correctly detected."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        todoitem_fields = analyzer.dataclasses["TodoItem"].fields
        assert "id" in todoitem_fields
        assert "name" in todoitem_fields
        assert "description" in todoitem_fields
        assert "completed" in todoitem_fields
        assert "difficulty" in todoitem_fields
        assert len(todoitem_fields) == 5

    def test_todo_state_fields(self, shared_datadir):
        """Test that State dataclass fields are correctly detected."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        state_fields = analyzer.dataclasses["State"].fields
        assert "count" in state_fields
        assert "todos" in state_fields
        assert len(state_fields) == 2

    def test_todo_routes(self, shared_datadir):
        """Test that all routes in todo.py are detected."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        route_names = [r.name for r in analyzer.routes]
        assert "index" in route_names
        assert "toggle_complete" in route_names
        assert "remove_todo" in route_names
        assert "edit_todo" in route_names
        assert "save_changes" in route_names
        assert "add_todo" in route_names
        assert "save_new" in route_names
        assert len(route_names) == 7

    def test_todo_helper_functions(self, shared_datadir):
        """Test that helper functions are tracked."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # index should call make_todo_list
        assert "make_todo_list" in analyzer.function_calls.get("index", [])
        
        # toggle_complete should call lookup_todo_item
        assert "lookup_todo_item" in analyzer.function_calls.get("toggle_complete", [])

    def test_todo_route_flow(self, shared_datadir):
        """Test that route flow is correctly captured."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # index should have Button to add_todo
        assert "add_todo" in analyzer.function_calls.get("index", [])
        
        # save_changes should call index
        assert "index" in analyzer.function_calls.get("save_changes", [])
        
        # save_new should call index
        assert "index" in analyzer.function_calls.get("save_new", [])
        
        # toggle_complete should call index
        assert "index" in analyzer.function_calls.get("toggle_complete", [])
        
        # remove_todo should call index
        assert "index" in analyzer.function_calls.get("remove_todo", [])

    def test_todo_attribute_usage(self, shared_datadir):
        """Test that attributes are tracked for usage."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # State.todos and State.count should be used
        assert "State" in analyzer.attribute_usage
        state_usage = analyzer.attribute_usage["State"]
        assert state_usage.get("todos", 0) > 0
        assert state_usage.get("count", 0) > 0
        
        # TodoItem attributes should be used
        assert "TodoItem" in analyzer.attribute_usage
        todoitem_usage = analyzer.attribute_usage["TodoItem"]
        assert todoitem_usage.get("name", 0) > 0
        assert todoitem_usage.get("completed", 0) > 0

    def test_todo_complexity(self, shared_datadir):
        """Test complexity calculation for todo.py."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # TodoItem has 5 primitive fields
        todoitem_complexity = analyzer._calculate_dataclass_complexity("TodoItem")
        assert todoitem_complexity == 0.5  # 5 primitives * 0.1

        # State has list[TodoItem]
        state_complexity = analyzer._calculate_dataclass_complexity("State")
        # count: int (0.1), todos: list[TodoItem] (1 for list)
        assert state_complexity > 1

    def test_todo_composition_relationship(self, shared_datadir):
        """Test that composition relationship is detected."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        # State should have dependency on TodoItem
        assert "TodoItem" in analyzer.dataclasses["State"].dependencies

    def test_todo_mermaid_diagrams(self, shared_datadir):
        """Test that diagrams are generated correctly."""
        with open(shared_datadir / "todo.py") as f:
            code = f.read()
        analyzer = Analyzer()
        analyzer.analyze(code)

        class_diagram = analyzer.generate_mermaid_class_diagram()
        assert "class TodoItem" in class_diagram
        assert "class State" in class_diagram
        assert "State --> TodoItem" in class_diagram

        function_diagram = analyzer.generate_mermaid_function_diagram()
        assert "index" in function_diagram
        # Multiple routes should call index
        assert function_diagram.count("index") > 1
