# This is a comment
from dataclasses import dataclass
from drafter import *


@dataclass
class State:
    x: int = 0
    y: str = "default"


def not_a_route(data: int):
    for something in otherwise:
        print(something)
    return data * 2


@route
def index(state: State) -> Page:
    return Page(state, ["Hello World!"])


@route(
    "/complex",
)
def complex(state: State) -> Page:  # This is a test
    """This is a docstring comment"""
    # This should be removed

    "Nice try, tuple"

    f"This was a {super} sneaky one"
    if state["x"] > 0:  # Nested Comment
        "Another sneaky docstring comment."
        return Page(state, ["Hello # World!"])
    else:

        return Page(state, [f"This is {allowed} a test", "Goodbye World!"])


print("This line should not be included")

start_server(State(5))


def unusual():
    while True:
        data = yield from get_data()
    return [data for data in data]


@route
def weird_stretch(state: State) -> Page:
    return Page(
        state,
        [
            "Hello" + "World",
            Button("Click me!", index),
            TextBox("new_name", state.x),
            Text("Oh yeah"),
        ],
    )
    # Test


# Test
