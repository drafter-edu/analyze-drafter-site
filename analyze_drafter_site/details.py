import ast
import builtins
import os
import tempfile
from collections import defaultdict
from typing import Dict, Optional

from mypy import build
from mypy.build import BuildSource
from mypy.nodes import FuncDef as MypyFuncDef
from mypy.options import Options
from mypy.types import Instance, UnionType

# Global variable of known component names
COMPONENTS = [
    "Argument",
    "Box",
    "BulletedList",
    "Button",
    "CheckBox",
    "Div",
    "Division",
    "Download",
    "FileUpload",
    "Header",
    "HorizontalRule",
    "Image",
    "LineBreak",
    "Link",
    "MatPlotLibPlot",
    "NumberedList",
    "Page",
    "PageContent",
    "Pre",
    "PreformattedText",
    "Row",
    "SelectBox",
    "Span",
    "SubmitButton",
    "Table",
    "Text",
    "TextArea",
    "TextBox",
]
LINKING_COMPONENT_NAMES = ["Link", "Button", "SubmitButton"]

# Cache of Python built-in names for performance
_BUILTIN_NAMES = frozenset(dir(builtins))


def is_builtin_name(name: str) -> bool:
    """Check if a name is a Python built-in function or type.

    Args:
        name: The function/type name to check

    Returns:
        True if the name is a built-in, False otherwise
    """
    return name in _BUILTIN_NAMES


class ClassInfo:
    def __init__(self, name, fields, base_classes):
        self.name = name
        self.fields = fields
        self.base_classes = base_classes
        self.dependencies = set()


class RouteInfo:
    def __init__(
        self,
        name,
        signature,
        components,
        fields_used,
        function_calls,
        unknown_relationships,
    ):
        self.name = name
        self.signature = signature
        self.components = components
        self.fields_used = fields_used
        self.function_calls = function_calls
        self.unknown_relationships = unknown_relationships


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.dataclasses = {}
        self.routes = []
        self.unknown_relationships = []
        self.current_class = None
        self.current_route = None
        self.current_function = None
        self.class_dependencies = defaultdict(set)
        self.function_calls = defaultdict(set)
        self.components_used = defaultdict(int)
        # Track attribute usage: {class_name: {field_name: count}}
        self.attribute_usage = defaultdict(lambda: defaultdict(int))
        # Variable type tracking: {variable_name: dataclass_name}
        # Built using mypy type inference
        self.variable_types: Dict[str, Optional[str]] = {}
        # Mypy result (set during analyze)
        self.mypy_result = None
        # Track user-defined function names for call graph filtering
        self.user_defined_functions = set()

    def visit_ClassDef(self, node):
        """Handle class definitions."""
        is_dataclass = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                is_dataclass = True

        if is_dataclass:
            fields = self.get_dataclass_fields(node)
            base_classes = [
                base.id for base in node.bases if isinstance(base, ast.Name)
            ]
            class_info = ClassInfo(node.name, fields, base_classes)
            self.dataclasses[node.name] = class_info
            # Note: Composition relationships are resolved in a second pass
            # after all dataclasses are discovered

        self.generic_visit(node)

    def get_dataclass_fields(self, node):
        """Extract the fields of a dataclass."""
        fields = {}
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(
                statement.target, ast.Name
            ):
                field_name = statement.target.id
                fields[field_name] = statement.annotation
        return fields

    def get_type_name(self, annotation):
        """Extract a readable type name from an AST annotation node."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            # For types like list[C], dict[str, int], etc.
            base = self.get_type_name(annotation.value)
            if isinstance(annotation.slice, ast.Name):
                slice_type = annotation.slice.id
                return f"{base}[{slice_type}]"
            elif isinstance(annotation.slice, ast.Tuple):
                slice_types = [
                    self.get_type_name(elt) for elt in annotation.slice.elts
                ]
                return f"{base}[{', '.join(slice_types)}]"
            elif isinstance(annotation.slice, ast.Subscript):
                # Handle nested subscripts like list[list[Tile]]
                slice_type = self.get_type_name(annotation.slice)
                return f"{base}[{slice_type}]"
            else:
                return base
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Attribute):
            # For types like typing.Optional
            return f"{self.get_type_name(annotation.value)}.{annotation.attr}"
        else:
            return (
                ast.unparse(annotation)
                if hasattr(ast, "unparse")
                else str(annotation)
            )

    def visit_FunctionDef(self, node):
        """Handle function definitions with @route decorator."""
        is_route = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "route":
                is_route = True
            elif isinstance(decorator, ast.Call):
                if (
                    isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "route"
                ):
                    is_route = True

        if is_route:
            signature = self.get_function_signature(node)
            self.current_route = RouteInfo(
                node.name, signature, defaultdict(int), set(), set(), []
            )
            self.routes.append(self.current_route)
            # Track function context for type resolution
            self.current_function = node.name
            # Visit the function body to collect information
            for stmt in node.body:
                self.visit(stmt)
            self.current_route = None
            self.current_function = None
        else:
            # Still visit non-route functions to track their existence
            old_function = getattr(self, "current_function", None)
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = old_function

    def visit_Call(self, node):
        """Handle function calls throughout the AST."""
        func_name = self.get_function_name(node)

        if func_name in COMPONENTS:
            # Track component usage
            if self.current_route:
                self.current_route.components[func_name] += 1
            self.components_used[func_name] += 1

            # Check if it's a linking component (Button, Link, SubmitButton)
            if func_name in LINKING_COMPONENT_NAMES and self.current_function:
                # The second argument (index 1) is the link target
                if len(node.args) >= 2:
                    target = node.args[1]
                    target_name = None

                    # Check if it's a direct function reference
                    if isinstance(target, ast.Name):
                        target_name = target.id
                    # Check if it's a string name
                    elif isinstance(target, ast.Constant) and isinstance(
                        target.value, str
                    ):
                        target_name = target.value
                        # Strip leading "/" from URLs
                        if target_name.startswith("/"):
                            target_name = target_name[1:]

                    if (
                        target_name
                        and target_name in self.user_defined_functions
                    ):
                        if self.current_route:
                            self.current_route.function_calls.add(target_name)
                        self.function_calls[self.current_function].add(
                            target_name
                        )
        elif func_name and self.current_function:
            # Track user-defined functions (not built-ins, methods, or
            # components). Check if this is a direct function call (not a
            # method call). Track calls from both routes and helper functions.
            if (
                isinstance(node.func, ast.Name)
                and func_name in self.user_defined_functions
            ):
                if self.current_route:
                    self.current_route.function_calls.add(func_name)
                self.function_calls[self.current_function].add(func_name)

        # Continue visiting child nodes
        self.generic_visit(node)

    def visit_Return(self, node):
        """Handle return statements that might call other functions."""
        if node.value and isinstance(node.value, ast.Call):
            func_name = self.get_function_name(node.value)
            # Track user-defined functions (not built-ins, methods, or components)
            # from both routes and helper functions.
            if (
                func_name
                and self.current_function
                and isinstance(node.value.func, ast.Name)
                and func_name in self.user_defined_functions
            ):
                if self.current_route:
                    self.current_route.function_calls.add(func_name)
                self.function_calls[self.current_function].add(func_name)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Handle attribute references to dataclass fields.

        Uses mypy type inference to accurately determine which dataclass
        a variable belongs to, rather than matching all dataclasses with
        the same field name.
        """
        if isinstance(node.value, ast.Name):
            # Check if this is accessing a field on a typed object
            if isinstance(node.ctx, ast.Load) or isinstance(
                node.ctx, ast.Store
            ):
                if self.current_route:
                    self.current_route.fields_used.add(node.attr)

                # Try to get the type from mypy analysis
                var_name = node.value.id
                dataclass_type = self._get_variable_type(var_name)

                if dataclass_type:
                    # We know the exact type from mypy!
                    if node.attr in self.dataclasses[dataclass_type].fields:
                        self.attribute_usage[dataclass_type][node.attr] += 1
                else:
                    # Fall back: match ALL dataclasses with this field
                    for class_name, class_info in self.dataclasses.items():
                        if node.attr in class_info.fields:
                            self.attribute_usage[class_name][node.attr] += 1
        # Handle nested attribute access (e.g., b.a.field1)
        elif isinstance(node.value, ast.Attribute):
            # Continue to track the attribute name
            if isinstance(node.ctx, ast.Load) or isinstance(
                node.ctx, ast.Store
            ):
                if self.current_route:
                    self.current_route.fields_used.add(node.attr)

                # Try to infer the type of the intermediate attribute
                intermediate_type = self._get_nested_type(node.value)

                if intermediate_type:
                    # We know the exact type!
                    if node.attr in self.dataclasses[intermediate_type].fields:
                        self.attribute_usage[intermediate_type][node.attr] += 1
                else:
                    # Fall back to old behavior
                    for class_name, class_info in self.dataclasses.items():
                        if node.attr in class_info.fields:
                            self.attribute_usage[class_name][node.attr] += 1
        self.generic_visit(node)

    def _get_variable_type(self, var_name):
        """Get the dataclass type of a variable using mypy information.

        Returns the dataclass name if known, None otherwise.
        """
        if not hasattr(self, "current_function") or not self.current_function:
            return None

        # Look up the type using function.variable format
        key = f"{self.current_function}.{var_name}"
        return self.variable_types.get(key)

    def _get_nested_type(self, attr_node):
        """Infer the type of a nested attribute access like b.a

        Given b.a.field1, this determines the type of 'a' by looking at
        the type of 'b' and finding the field 'a' in that dataclass.

        Returns the dataclass name if it can be determined, None otherwise.
        """
        if isinstance(attr_node.value, ast.Name):
            # Base case: b.a
            base_var = attr_node.value.id
            base_type = self._get_variable_type(base_var)

            if base_type and base_type in self.dataclasses:
                # Look up the field type
                field_name = attr_node.attr
                if field_name in self.dataclasses[base_type].fields:
                    field_type_node = self.dataclasses[base_type].fields[
                        field_name
                    ]
                    field_type = self.get_type_name(field_type_node)
                    # Extract base type (handle list[X], etc.)
                    field_type_base = field_type.split("[")[0]
                    if field_type_base in self.dataclasses:
                        return field_type_base
        elif isinstance(attr_node.value, ast.Attribute):
            # Recursive case: c.b.a
            # First get the type of c.b
            intermediate_type = self._get_nested_type(attr_node.value)
            if intermediate_type and intermediate_type in self.dataclasses:
                # Then get the type of the field 'a' in that type
                field_name = attr_node.attr
                if field_name in self.dataclasses[intermediate_type].fields:
                    field_type_node = self.dataclasses[
                        intermediate_type
                    ].fields[field_name]
                    field_type = self.get_type_name(field_type_node)
                    field_type_base = field_type.split("[")[0]
                    if field_type_base in self.dataclasses:
                        return field_type_base

        return None

    def get_function_name(self, node):
        """Get the name of a function or method being called."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def get_function_signature(self, node):
        """Extract the function signature."""
        params = [arg.arg for arg in node.args.args]
        return f"{node.name}({', '.join(params)})"

    def _run_mypy_analysis(self, code: str):
        """Run mypy to get type information for variables.

        This populates self.variable_types with mappings from variable names
        to their dataclass types (if applicable).
        """
        # Write code to a temporary file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Build with mypy
            options = Options()
            options.python_version = (3, 12)
            options.show_traceback = False
            options.incremental = False
            options.ignore_missing_imports = True

            sources = [BuildSource(temp_file, "__main__", None)]

            try:
                result = build.build(sources, options)
                self.mypy_result = result

                # Extract type information from the main module
                if "__main__" in result.graph:
                    main_tree = result.graph["__main__"].tree
                    self._extract_variable_types(main_tree)
            except Exception:
                # If mypy fails, we'll fall back to the old behavior
                pass
        finally:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

    def _extract_variable_types(self, tree):
        """Extract variable type information from mypy tree."""
        for name, symbol in tree.names.items():
            node = symbol.node

            # Handle function definitions to get parameter types
            if isinstance(node, MypyFuncDef):
                self._extract_func_params(node)
            elif hasattr(node, "func") and isinstance(node.func, MypyFuncDef):
                # Handle decorated functions (e.g., @route)
                self._extract_func_params(node.func)

    def _extract_func_params(self, func_def):
        """Extract parameter types from a function definition."""
        for arg in func_def.arguments:
            var = arg.variable
            if var.type:
                type_name = self._get_type_name_from_mypy(var.type)
                if type_name:
                    # Store the mapping for this function's scope
                    # We'll use function_name.var_name as key
                    self.variable_types[f"{func_def.name}.{var.name}"] = (
                        type_name
                    )

    def _get_type_name_from_mypy(self, mypy_type):
        """Extract the dataclass name from a mypy type.

        Returns the class name if it's a dataclass we're tracking,
        None otherwise.
        """
        if isinstance(mypy_type, Instance):
            # Get the full name, e.g., "__main__.State"
            fullname = mypy_type.type.fullname
            # Extract just the class name
            if "." in fullname:
                class_name = fullname.split(".")[-1]
            else:
                class_name = fullname

            # Only return if it's a dataclass we're tracking
            if class_name in self.dataclasses:
                return class_name
        elif isinstance(mypy_type, UnionType):
            # For Union types, try to find a dataclass in the union
            for item in mypy_type.items:
                type_name = self._get_type_name_from_mypy(item)
                if type_name:
                    return type_name

        return None

    def analyze(self, code):
        """Run analysis on the provided Python code."""
        tree = ast.parse(code)

        # First pass: discover dataclasses and user-defined functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.visit_ClassDef(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Track all user-defined functions for call graph filtering
                self.user_defined_functions.add(node.name)

        # Second pass: run mypy to get type information
        # This must happen after dataclass discovery but before
        # we traverse function bodies
        self._run_mypy_analysis(code)

        # Third pass: visit the full tree to analyze routes and usage
        self.visit(tree)

        # Fourth pass: resolve composition relationships
        self._resolve_class_dependencies()

    def _resolve_class_dependencies(self):
        """Resolve composition relationships between dataclasses."""
        for class_name, class_info in self.dataclasses.items():
            class_info.dependencies.clear()
            for field_name, field_type in class_info.fields.items():
                type_name = self.get_type_name(field_type)
                # Extract potential type references
                # Note: This handles simple cases like list[C] or
                # dict[str, C] but may not handle deeply nested types
                self._extract_type_references(
                    type_name, class_name, class_info.dependencies
                )

    def _extract_type_references(self, type_name, owner_class, dependencies):
        """Extract dataclass references from a type name."""
        # Handle base type (e.g., "A" from "A" or "list[A]")
        base_type = type_name.split("[")[0]
        if base_type in self.dataclasses and base_type != owner_class:
            dependencies.add(base_type)

        # Handle subscripted types like list[C] or dict[str, C]
        if "[" in type_name and "]" in type_name:
            inner_type = type_name[
                type_name.index("[") + 1 : type_name.rindex("]")  # noqa: E203
            ]  # E203 is a known conflict with Black's slice formatting
            # Split by comma to handle types like dict[str, int]
            for inner in inner_type.split(","):
                inner = inner.strip()
                # Recursively extract from nested types
                if inner in self.dataclasses and inner != owner_class:
                    dependencies.add(inner)
                elif "[" in inner:
                    # Handle nested generics (basic support)
                    self._extract_type_references(
                        inner, owner_class, dependencies
                    )

    def _calculate_field_complexity(self, type_name):
        """Calculate complexity score for a single field type.

        Complexity scoring:
        - Primitives (int, str, bool, float): 0.1
        - Lists: 1
        - Lists with nested structures
          (list[list[...]] or list[Dataclass]): 10
        - Custom dataclasses: 1
        - Dicts, tuples, sets: 10
        - Any other: 100
        """
        # Handle subscripted types like list[X], dict[X, Y]
        base_type = type_name.split("[")[0].lower()

        # Check for primitives
        if base_type in ["int", "str", "bool", "float"]:
            return 0.1

        # Check for lists
        if base_type == "list":
            # Check if it's a nested structure
            # (list[list[...]] or list[Dataclass])
            if "[" in type_name:
                # Extract the inner type from list[X]
                inner_type = type_name[
                    type_name.index("[") + 1 : type_name.rindex("]")  # noqa
                ]  # E203 is a known conflict with Black's slice formatting
                # Check if inner type is a nested structure
                # (contains '[') or is a dataclass
                inner_base = inner_type.split("[")[0].strip()
                if "[" in inner_type or inner_base in self.dataclasses:
                    return 10
            return 1

        # Check for custom dataclasses
        if type_name.split("[")[0] in self.dataclasses:
            return 1

        # Check for dict, tuple, set
        if base_type in ["dict", "tuple", "set"]:
            return 10

        # Any other type
        return 100

    def _calculate_dataclass_complexity(self, class_name):
        """Calculate total complexity score for a dataclass."""
        class_info = self.dataclasses[class_name]
        total_score = 0.0
        for field_type in class_info.fields.values():
            type_name = self.get_type_name(field_type)
            total_score += self._calculate_field_complexity(type_name)
        return total_score

    def get_dataclass_attribute_csv(self):
        """Generate CSV table of dataclass attributes with usage and
        complexity."""
        if not self.dataclasses:
            return "No dataclasses found."

        output = []
        output.append("Dataclass,Attribute,Type,Usage Count,Complexity")

        for class_name, class_info in self.dataclasses.items():
            for field_name, field_type in class_info.fields.items():
                type_name = self.get_type_name(field_type)
                usage_count = self.attribute_usage[class_name][field_name]
                field_complexity = self._calculate_field_complexity(type_name)

                output.append(
                    f"{class_name},{field_name},{type_name},"
                    f"{usage_count},{field_complexity:.1f}"
                )

        return "\n".join(output)

    def get_dataclass_complexity_csv(self):
        """Generate CSV table of dataclass complexity scores."""
        if not self.dataclasses:
            return ""

        output = []
        output.append("Dataclass,Complexity")

        total_complexity = 0.0
        for class_name in self.dataclasses.keys():
            complexity = self._calculate_dataclass_complexity(class_name)
            total_complexity += complexity
            output.append(f"{class_name},{complexity:.1f}")

        output.append(f"TOTAL,{total_complexity:.1f}")

        return "\n".join(output)

    def get_unused_fields_csv(self):
        """Generate CSV table of unused dataclass fields."""
        if not self.dataclasses:
            return ""

        output = []
        output.append("Dataclass,Attribute")

        # Collect all unused attributes
        for class_name, class_info in self.dataclasses.items():
            for field_name in class_info.fields.keys():
                if self.attribute_usage[class_name][field_name] == 0:
                    output.append(f"{class_name},{field_name}")

        # If only header exists, return empty string
        if len(output) == 1:
            return ""

        return "\n".join(output)

    def get_unused_warnings(self):
        """Generate warnings about unused dataclasses and attributes."""
        if not self.dataclasses:
            return ""

        output = []

        # Check for unused dataclasses
        unused_dataclasses = []
        for class_name, class_info in self.dataclasses.items():
            class_used = (
                any(
                    class_name in info.dependencies
                    for info in self.dataclasses.values()
                )
                or sum(self.attribute_usage[class_name].values()) > 0
            )
            if not class_used:
                unused_dataclasses.append(class_name)

        if unused_dataclasses:
            output.append(
                "WARNING: The following dataclasses are NOT used anywhere:"
            )
            for dc in unused_dataclasses:
                output.append(f"  {dc}")

        # Check for unused attributes
        unused_attributes = []
        for class_name, class_info in self.dataclasses.items():
            for field_name in class_info.fields.keys():
                if self.attribute_usage[class_name][field_name] == 0:
                    unused_attributes.append(f"{class_name}.{field_name}")

        if unused_attributes:
            if output:
                output.append("")  # Add blank line between warnings
            output.append(
                "WARNING: The following attributes are NOT used anywhere:"
            )
            for attr in unused_attributes:
                output.append(f"  {attr}")

        return "\n".join(output) if output else ""

    def get_textual_details(self):
        """Generate textual details about dataclasses and routes."""
        output = []

        # Dataclasses listing
        if self.dataclasses:
            output.append("Dataclasses:")
            for class_info in self.dataclasses.values():
                output.append(f"{class_info.name}")
                for field in class_info.fields:
                    output.append(f"  {field}")
            output.append("")

        # Routes listing
        if self.routes:
            output.append("Routes:")
            for route_info in self.routes:
                output.append(f"{route_info.signature}")
                for component, count in route_info.components.items():
                    output.append(f"  {component}: {count}")
                for field in route_info.fields_used:
                    output.append(f"  {field} used")
                for func_call in route_info.function_calls:
                    output.append(f"  calls {func_call}")
                for unknown in route_info.unknown_relationships:
                    output.append(f"  unknown relationship: {unknown}")

        return "\n".join(output)

    def generate_dataclass_analysis(self):
        """Generate detailed analysis of dataclasses with usage and
        complexity."""
        if not self.dataclasses:
            return "No dataclasses found.\n"

        output = []

        # Build table data
        table_data = []
        total_complexity = 0.0
        unused_dataclasses = []

        for class_name, class_info in self.dataclasses.items():
            # Check if dataclass is used at all
            class_used = (
                any(
                    class_name in info.dependencies
                    for info in self.dataclasses.values()
                )
                or sum(self.attribute_usage[class_name].values()) > 0
            )

            if not class_used:
                unused_dataclasses.append(class_name)

            complexity_score = self._calculate_dataclass_complexity(class_name)
            total_complexity += complexity_score

            # List all attributes with their types and usage counts
            for field_name, field_type in class_info.fields.items():
                type_name = self.get_type_name(field_type)
                usage_count = self.attribute_usage[class_name][field_name]
                field_complexity = self._calculate_field_complexity(type_name)

                table_data.append(
                    [
                        class_name,
                        field_name,
                        type_name,
                        usage_count,
                        f"{field_complexity:.1f}",
                    ]
                )

        # Generate CSV-style table with header
        output.append("Dataclass,Attribute,Type,Usage Count,Complexity")
        for row in table_data:
            output.append(",".join(str(x) for x in row))

        output.append("-" * 80)

        # Complexity scores table - also CSV format
        output.append("Dataclass,Complexity")
        for class_name in self.dataclasses.keys():
            complexity = self._calculate_dataclass_complexity(class_name)
            output.append(f"{class_name},{complexity:.1f}")
        output.append(f"TOTAL,{total_complexity:.1f}")

        output.append("-" * 80)

        # Report unused dataclasses (textual section)
        if unused_dataclasses:
            output.append(
                "WARNING: The following dataclasses are NOT used anywhere:"
            )
            for dc in unused_dataclasses:
                output.append(f"  {dc}")
            output.append("-" * 80)

        # Report unused attributes (textual section)
        unused_attributes = []
        for class_name, class_info in self.dataclasses.items():
            for field_name in class_info.fields.keys():
                if self.attribute_usage[class_name][field_name] == 0:
                    unused_attributes.append(f"{class_name}.{field_name}")

        if unused_attributes:
            output.append(
                "WARNING: The following attributes are NOT used anywhere:"
            )
            for attr in unused_attributes:
                output.append(f"  {attr}")
            output.append("-" * 80)

        return "\n".join(output)

    def generate_mermaid_class_diagram(self):
        """Generate Mermaid diagram for class relationships."""
        mermaid = "classDiagram\n"
        for class_name, class_info in self.dataclasses.items():
            mermaid += f"    class {class_name} {{\n"
            for field, annotation in class_info.fields.items():
                type_name = self.get_type_name(annotation)
                mermaid += f"        {type_name} {field}\n"
            mermaid += "    }\n"
            for dep in class_info.dependencies:
                # Only show arrows to other dataclasses that exist in this file
                # Built-in types and external types are tracked but not shown
                if dep in self.dataclasses:
                    mermaid += f"    {class_name} --> {dep}\n"
        return mermaid

    def generate_mermaid_function_diagram(self):
        """Generate Mermaid diagram for function relationships."""
        mermaid = "graph TD\n"
        # Only show relationships if there are any
        if self.function_calls:
            for func, calls in self.function_calls.items():
                for called_func in calls:
                    mermaid += f"    {func} --> {called_func}\n"
        return mermaid

    def save_results(self):
        """Save the results to files."""
        with open("dataclasses.txt", "w") as f:
            for class_info in self.dataclasses.values():
                f.write(f"{class_info.name}\n")
                for field in class_info.fields:
                    f.write(f"  {field}\n")

        with open("routes.txt", "w") as f:
            for route_info in self.routes:
                f.write(f"{route_info.name} {route_info.signature}\n")
                for component, count in route_info.components.items():
                    f.write(f"  {component}: {count}\n")
                for field in route_info.fields_used:
                    f.write(f"  {field} used\n")
                for func_call in route_info.function_calls:
                    f.write(f"  calls {func_call}\n")
                for unknown in route_info.unknown_relationships:
                    f.write(f"  unknown relationship: {unknown}\n")

        with open("class_diagram.mmd", "w") as f:
            f.write(self.generate_mermaid_class_diagram())

        with open("function_diagram.mmd", "w") as f:
            f.write(self.generate_mermaid_function_diagram())

    def save_as_string(self):
        """Save the results to strings."""
        # New detailed dataclass analysis
        dataclass_analysis = self.generate_dataclass_analysis()

        # Old simple format
        dataclasses = "Dataclasses:\n"
        for class_info in self.dataclasses.values():
            dataclasses += f"{class_info.name}\n"
            for field in class_info.fields:
                dataclasses += f"  {field}\n"

        routes = "Routes:\n"
        for route_info in self.routes:
            routes += f"{route_info.signature}\n"
            for component, count in route_info.components.items():
                routes += f"  {component}: {count}\n"
            for field in route_info.fields_used:
                routes += f"  {field} used\n"
            for func_call in route_info.function_calls:
                routes += f"  calls {func_call}\n"
            for unknown in route_info.unknown_relationships:
                routes += f"  unknown relationship: {unknown}\n"

        class_diagram = self.generate_mermaid_class_diagram()
        function_diagram = self.generate_mermaid_function_diagram()

        return (
            dataclass_analysis,
            dataclasses,
            routes,
            class_diagram,
            function_diagram,
        )
