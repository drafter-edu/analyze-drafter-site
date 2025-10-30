from drafter import *


@dataclass
class TodoItem:
    """
    An individual list item that should be done.

    Attributes:
        id (int): A unique identifier for the to-do item.
        name (str): The name of the to-do item.
        description (str): A detailed description of the to-do item.
        completed (bool): A boolean indicating whether the to-do item has been completed.
        difficulty (int): An integer rating (1-3) indicating the difficulty of the to-do item.
    """

    id: int
    name: str
    description: str
    completed: bool
    difficulty: int


@dataclass
class State:
    """
    The state of the to-do application, containing a list of to-do items.

    Attributes:
        count (int): The total number of to-do items that have ever been created. Used to assign unique IDs.
        todos (list[TodoItem]): A list of TodoItem objects representing the to-do items.
    """

    count: int
    todos: list[TodoItem]


@route
def index(state: State) -> Page:
    """
    Display the main to-do list page.

    Args:
        state (State): The current state of the to-do application.

    Returns:
        Page: The rendered to-do list page.
    """
    current_items = make_todo_list(state.todos)

    return Page(
        state,
        [
            Header("To-Do List"),
            "Add and manage your to-do items.",
            Button("Add New To-Do", "add_todo"),
            Div(current_items),
        ],
    )


def make_todo_toggle(completed: bool, target_id: Argument) -> Button:
    """
    Creates a button to toggle the completion status of a to-do item.

    Args:
        completed (bool): The current completion status of the to-do item.
        target_id (Argument): The unique ID of the to-do item.
    Returns:
        Button: A button that displays a checked or unchecked box based on the completion status.
    """
    if completed:
        return Button("☑️", "toggle_complete", target_id)
    else:
        return Button("🔲", "toggle_complete", target_id)


def make_todo_list(todos: list[TodoItem]) -> PageContent:
    """
    Generates a page content displaying a list of to-do items.

    Args:
        todos (list[TodoItem]): A list of TodoItem objects representing the to-do items.

    Returns:
        PageContent: A page content object containing either a message indicating no to-do items,
        or a table displaying each to-do item with its name, difficulty, description, and action buttons
        for toggling completion, removing, and editing the item.
    """
    if not todos:
        return Div("No to-do items yet.")

    items = []
    for todo in todos:
        difficulty = "⭐" * todo.difficulty
        target_id = Argument("target_id", todo.id)
        items.append(
            [
                make_todo_toggle(todo.completed, target_id),
                Div(
                    todo.name,
                    difficulty,
                    LineBreak(),
                    small_font(Text(todo.description)),
                ),
                Button("Remove", "remove_todo", target_id),
                Button("Edit", "edit_todo", target_id),
            ]
        )
    return Table(items)


def lookup_todo_item(todos: list[TodoItem], target_id: int) -> TodoItem:
    """
    Looks up a to-do item by its unique ID.

    Args:
        todos (list[TodoItem]): A list of TodoItem objects representing the to-do items.
        target_id (int): The unique ID of the to-do item to look up.

    Returns:
        TodoItem: The to-do item with the specified ID.
    """
    for todo in todos:
        if todo.id == target_id:
            return todo
    return None


@route
def toggle_complete(state: State, target_id: int) -> Page:
    """
    Toggles the completion status of a to-do item.

    Args:
        state (State): The current state of the to-do application.
        target_id (int): The unique ID of the to-do item to toggle.

    Returns:
        Page: The updated to-do list page.
    """
    todo = lookup_todo_item(state.todos, target_id)
    if todo:
        todo.completed = not todo.completed
    return index(state)


@route
def remove_todo(state: State, target_id: int) -> Page:
    """
    Removes a to-do item from the list.

    Args:
        state (State): The current state of the to-do application.
        target_id (int): The unique ID of the to-do item to remove.

    Returns:
        Page: The updated to-do list page.
    """
    new_todos = []
    for todo in state.todos:
        if todo.id != target_id:
            new_todos.append(todo)
    state.todos = new_todos
    return index(state)


DIFFICULTY_RATINGS = ["1", "2", "3"]


@route
def edit_todo(state: State, target_id: int) -> Page:
    """
    Displays the edit page for a specific to-do item.

    Args:
        state (State): The current state of the to-do application.
        target_id (int): The unique ID of the to-do item to edit.
    Returns:
        Page: The edit page for the specified to-do item.
    """
    editing = lookup_todo_item(state.todos, target_id)
    return Page(
        state,
        [
            Header("Edit:"),
            Row("Name:", TextBox("new_name", editing.name)),
            Row(
                "Difficulty:",
                SelectBox(
                    "new_difficulty", DIFFICULTY_RATINGS, str(editing.difficulty)
                ),
            ),
            Row("Description:", TextArea("new_description", editing.description)),
            Button("Save Changes", "save_changes", Argument("target_id", target_id)),
            Button("Cancel", "index"),
        ],
    )


@route
def save_changes(
    state: State,
    new_name: str,
    new_difficulty: int,
    new_description: str,
    target_id: int,
) -> Page:
    """Saves the changes made to a to-do item.

    Args:
        state (State): The current state of the to-do application.
        new_name (str): The new name for the to-do item.
        new_difficulty (int): The new difficulty level for the to-do item.
        new_description (str): The new description for the to-do item.
        target_id (int): The unique ID of the to-do item to update.

    Returns:
        Page: The updated to-do list page.
    """
    todo = lookup_todo_item(state.todos, target_id)
    if todo:
        todo.name = new_name
        todo.difficulty = new_difficulty
        todo.description = new_description

    return index(state)


@route
def add_todo(state: State) -> Page:
    """
    Displays the page to add a new to-do item.
    Args:
        state (State): The current state of the to-do application.
    Returns:
        Page: The page to add a new to-do item.
    """
    return Page(
        state,
        [
            Header("Create New Todo"),
            Row("Name:", TextBox("new_name", "")),
            Row(
                "Difficulty:",
                SelectBox("new_difficulty", DIFFICULTY_RATINGS, "1"),
            ),
            Row("Description:", TextArea("new_description", "")),
            Button("Save Changes", "save_new"),
            Button("Cancel", "index"),
        ],
    )


@route
def save_new(
    state: State, new_name: str, new_difficulty: int, new_description: str
) -> Page:
    """
    Saves a new to-do item to the list. This will increase the count of total
    to-do items ever created, and use that as the unique ID for the new item.

    Args:
        state (State): The current state of the to-do application.
        new_name (str): The name of the new to-do item.
        new_difficulty (int): The difficulty level of the new to-do item.
        new_description (str): The description of the new to-do item.
    Returns:
        Page: The updated to-do list page.
    """
    state.count += 1
    new_todo = TodoItem(
        state.count,
        new_name,
        new_description,
        False,
        new_difficulty,
    )
    state.todos.append(new_todo)
    return index(state)


start_server(
    State(
        1, [TodoItem(0, "Write todo list", "Write a few items to get done.", False, 1)]
    )
)
