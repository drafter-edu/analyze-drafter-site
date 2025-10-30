import ast
from collections import defaultdict

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
        self.class_dependencies = defaultdict(set)
        self.function_calls = defaultdict(set)
        self.components_used = defaultdict(int)

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

            # Detect composition relationships
            for field_name, field_type in fields.items():
                type_name = self.get_type_name(field_type)
                # Extract the base type name (e.g., "A" from "A" or "list[A]")
                base_type = type_name.split("[")[0]
                if base_type in self.dataclasses or "[" in type_name:
                    # Check if it's a reference to another dataclass
                    if base_type != node.name:  # Avoid self-references
                        class_info.dependencies.add(base_type)
                    # For subscripted types like list[C], extract C
                    if "[" in type_name and "]" in type_name:
                        inner_type = type_name[
                            type_name.index("[") + 1: type_name.rindex("]")
                        ]
                        # Handle comma-separated types like dict[str, int]
                        for inner in inner_type.split(","):
                            inner = inner.strip()
                            if inner != node.name:  # Avoid self-references
                                class_info.dependencies.add(inner)

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
            # Visit the function body to collect information
            for stmt in node.body:
                self.visit(stmt)
            self.current_route = None
        else:
            # Still visit non-route functions to track their existence
            self.generic_visit(node)

    def visit_Call(self, node):
        """Handle function calls throughout the AST."""
        func_name = self.get_function_name(node)

        if func_name in COMPONENTS:
            # Track component usage
            if self.current_route:
                self.current_route.components[func_name] += 1
            self.components_used[func_name] += 1

            # Check if it's a linking component (Button, Link, SubmitButton)
            if func_name in LINKING_COMPONENT_NAMES and self.current_route:
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

                    if target_name:
                        self.current_route.function_calls.add(target_name)
                        self.function_calls[self.current_route.name].add(
                            target_name
                        )
        else:
            # Track function calls
            if func_name and self.current_route:
                self.current_route.function_calls.add(func_name)
                self.function_calls[self.current_route.name].add(func_name)

        # Continue visiting child nodes
        self.generic_visit(node)

    def visit_Return(self, node):
        """Handle return statements that might call other route functions."""
        if node.value and isinstance(node.value, ast.Call):
            func_name = self.get_function_name(node.value)
            if func_name and self.current_route:
                self.current_route.function_calls.add(func_name)
                self.function_calls[self.current_route.name].add(func_name)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Handle attribute references to dataclass fields."""
        if isinstance(node.value, ast.Name) and self.current_route:
            # Check if this is accessing a field on a state object
            # We'll track any attribute access for now
            if isinstance(node.ctx, ast.Load) or isinstance(
                node.ctx, ast.Store
            ):
                self.current_route.fields_used.add(node.attr)
        self.generic_visit(node)

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

    def analyze(self, code):
        """Run analysis on the provided Python code."""
        tree = ast.parse(code)
        self.visit(tree)

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
                # Only show dependencies to other dataclasses that exist
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

        return dataclasses, routes, class_diagram, function_diagram
