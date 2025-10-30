from drafter import *
from dataclasses import dataclass

add_website_css(
    ".comment-line",
    "display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #ccc;",
)


@dataclass
class Line:
    """
    A line of code with an optional comment.
    Attributes:
        original (str): The original line of code.
        comment (str): The comment associated with the line of code.
        index (int): The line number in the original text.
    """

    original: str
    comment: str
    index: int


@dataclass
class State:
    """
    The state of the code commenter application.

    Attributes:
        comments (list[Line]): A list of Line objects representing the code lines and their comments.
        original_text (str): The original text of the code being commented on.
    """

    comments: list[Line]
    original_text: str


def parse_lines(text: str) -> list[Line]:
    """
    Parses the input text into a list of Line objects.

    Args:
        text (str): The input text to parse.
    Returns:
        list[Line]: A list of Line objects.
    """
    lines = []
    for i, line in enumerate(text.split("\n")):
        lines.append(Line(line.rstrip(), "", i))
    return lines


@route
def index(state: State) -> Page:
    """
    Display the main page of the code commenter application.

    Args:
        state (State): The current state of the application.
    Returns:
        Page: The rendered main page.
    """
    return Page(
        state,
        [
            Header("Code Commenter"),
            "Upload a file or type some code to get started.",
            FileUpload("code_file"),
            TextArea("text_box", state.original_text),
            Button("Start", "start_commenting"),
        ],
    )


@route
def error_page(message: str) -> Page:
    """
    Display an error page with the given message.

    Args:
        message (str): The error message to display.
    Returns:
        Page: The rendered error page.
    """
    return Page(
        None,
        [
            Header("Error"),
            f"Error: {message}",
            Button("Back", "index"),
        ],
    )


@route
def start_commenting(state: State, code_file: str = "", text_box: str = "") -> Page:
    """
    Starts the commenting process by parsing the input text or file.

    Args:
        state (State): The current state of the application.
        code_file (str): The content of the uploaded file (if any).
        text_box (str): The content of the text area (if any).
    Returns:
        Page: The page displaying the code lines for commenting.
    """
    if code_file:
        text = code_file
    elif text_box:
        text = text_box
    else:
        return error_page("Please upload a file or enter some text.")

    lines = parse_lines(text)
    state.comments = lines
    state.original_text = text

    return page_commenter(state)


@route
def page_commenter(state: State) -> Page:
    """
    Displays the page for commenting on code lines.

    Args:
        state (State): The current state of the application.
    Returns:
        Page: The page displaying the code lines for commenting.
    """
    content = [Header("Code Commenter")]
    for line in state.comments:
        if line.original:
            content.append(
                Div(
                    line.original,
                    Button("💬", "comment", Argument("index", line.index)),
                    classes="comment-line",
                )
            )
        else:
            content.append(Div(classes="comment-line", style_height="1.5em"))
        if line.comment:
            content.append(Div(small_font(line.comment), classes="comment-line"))

    content.append(Button("Reset", "index"))

    return Page(state, content)


@route
def comment(state: State, index: int) -> Page:
    """
    Displays the comment box for a specific line of code.

    Args:
        state (State): The current state of the application.
        index (int): The index of the line to comment on.
    Returns:
        Page: The page displaying the comment box for the specified line.
    """
    comment = state.comments[index]
    return Page(
        state,
        [
            Header("Add Comment"),
            PreformattedText(comment.original),
            TextArea("comment_box", comment.comment),
            Button(
                "Save Comment",
                "save_comment",
                arguments=Argument("index", index),
            ),
            Button("Back", "page_commenter"),
        ],
    )


@route
def save_comment(state: State, index: int, comment_box: str) -> Page:
    """
    Saves the comment for a specific line of code.

    Args:
        state (State): The current state of the application.
        index (int): The index of the line to save the comment for.
        comment_box (str): The content of the comment box.
    Returns:
        Page: The updated page displaying the code lines for commenting.
    """
    state.comments[index].comment = comment_box
    return page_commenter(state)


start_server(State([], ""))
