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

    def visit_FunctionDef(self, node):
        """Handle function definitions with @route decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "route":
                signature = self.get_function_signature(node)
                self.current_route = RouteInfo(
                    node.name, signature, defaultdict(int), set(), set(), []
                )
                self.routes.append(self.current_route)
                self.visit_FunctionBody(node)
                self.current_route = None
        self.generic_visit(node)

    def visit_FunctionBody(self, node):
        """Analyze the body of the function for references."""
        for statement in node.body:
            if isinstance(statement, ast.Call):
                self.handle_function_call(statement)
            if isinstance(statement, ast.Attribute):
                self.handle_attribute_use(statement)

    def handle_function_call(self, node):
        """Handle function calls."""
        func_name = self.get_function_name(node)
        if func_name in COMPONENTS:
            self.components_used[func_name] += 1
        elif func_name in self.function_calls:
            if self.current_route is None:
                return
            self.function_calls[self.current_route.name].add(func_name)
        else:
            self.unknown_relationships.append(ast.dump(node))

    def handle_attribute_use(self, node):
        """Handle attribute references to dataclass fields."""
        if (
            isinstance(node.value, ast.Name)
            and node.attr in self.dataclasses.get(node.value.id, {}).fields
        ):
            if self.current_route is None:
                return
            self.current_route.fields_used.add(node.attr)

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
            mermaid += f"class {class_name} {{\n"
            for field, annotation in class_info.fields.items():
                mermaid += f"  {field}: {ast.dump(annotation)}\n"
            mermaid += "}\n"
            for dep in class_info.dependencies:
                mermaid += f"{class_name} --> {dep}\n"
        return mermaid

    def generate_mermaid_function_diagram(self):
        """Generate Mermaid diagram for function relationships."""
        mermaid = "graph TD\n"
        for func, calls in self.function_calls.items():
            for called_func in calls:
                mermaid += f"{func} --> {called_func}\n"
        for unknown in self.unknown_relationships:
            mermaid += f"unknown --> {unknown}\n"
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
