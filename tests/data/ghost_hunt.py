from drafter import *
from dataclasses import dataclass
from random import choice, shuffle, seed


@dataclass
class Tile:
    """
    Represents a tile on the game board.

    Attributes:
        text (str): The text displayed on the tile (e.g., ghost, treat, or empty).
        flipped (bool): Whether the tile has been flipped or not.
        x (int): The x-coordinate of the tile on the grid.
        y (int): The y-coordinate of the tile on the grid.
    """

    text: str
    flipped: bool
    x: int
    y: int


@dataclass
class State:
    """
    Represents the state of the game.

    Attributes:
        grid (list[list[Tile]]): The game board represented as a grid of tiles.
        seed (int): The seed value used for randomizing the game board.
        score (int): The current score of the player.
        size (int): The size of the game board (size x size).
        ghosts (int): The total number of ghosts hidden on the board.
    """

    grid: list[list[Tile]]
    seed: int
    score: int
    size: int
    ghosts: int


GHOST = "👻"
EMPTY = "⬜"
TREAT = "🍬"


def make_ghost_grid(seed_value: int, size: int, ghosts: int) -> list[list[Tile]]:
    """
    Generates a game board with ghosts and treats.

    Args:
        seed_value (int): The seed value for randomization.
        size (int): The size of the grid (size x size).
        ghosts (int): The number of ghosts to place on the board.
    Returns:
        list[list[Tile]]: The generated game board as a grid of tiles.
    """
    seed(seed_value)
    grid = make_empty_grid(size)
    positions = choose_ghost_spots(grid, ghosts)
    fill_in_board(grid, positions)
    return grid


def make_empty_grid(size: int) -> list[list[Tile]]:
    """
    Creates an empty game board of the specified size.

    Args:
        size (int): The size of the grid (size x size).
    Returns:
        list[list[Tile]]: An empty grid of tiles.
    """
    grid = []
    for y in range(size):
        row = []
        for x in range(size):
            row.append(Tile(EMPTY, False, x, y))
        grid.append(row)
    return grid


def choose_ghost_spots(grid: list[list[Tile]], ghosts: int) -> list[list[int]]:
    """
    Randomly selects positions on the grid to place ghosts.

    Args:
        grid (list[list[Tile]]): The game board grid.
        ghosts (int): The number of ghosts to place.
    Returns:
        list[list[int]]: A list of [x, y] positions for the ghosts.
            The inner list will always have length 2.
    """
    size = len(grid)
    ys = list(range(size))
    xs = list(range(size))
    shuffle(xs)
    shuffle(ys)
    positions = []
    for ghost in range(ghosts):
        positions.append([xs.pop(), ys.pop()])
    return positions


def add_treat_if_empty(grid: list[list[Tile]], x: int, y: int):
    """
    Adds a treat to the specified position on the grid if it is empty.

    Args:
        grid (list[list[Tile]]): The game board grid.
        x (int): The x-coordinate of the position.
        y (int): The y-coordinate of the position.
    """
    if x < 0 or y < 0 or y >= len(grid) or x >= len(grid):
        return
    if grid[y][x].text == EMPTY:
        grid[y][x].text = TREAT


def fill_in_board(grid: list[list[Tile]], positions: list[tuple[int, int]]):
    """
    Fills in the game board with ghosts and treats based on the specified ghost positions.

    Args:
        grid (list[list[Tile]]): The game board grid.
        positions (list[tuple[int, int]]): A list of [x, y]
            positions where ghosts should be placed.
    """
    for x, y in positions:
        grid[y][x].text = GHOST
        add_treat_if_empty(grid, x + 1, y)
        add_treat_if_empty(grid, x - 1, y)
        add_treat_if_empty(grid, x, y + 1)
        add_treat_if_empty(grid, x, y - 1)
        add_treat_if_empty(grid, x + 1, y + 1)
        add_treat_if_empty(grid, x - 1, y - 1)
        add_treat_if_empty(grid, x + 1, y - 1)
        add_treat_if_empty(grid, x - 1, y + 1)


@route
def index(state: State) -> Page:
    """
    The main page of the game, where players can start a new game.

    Args:
        state (State): The current state of the game.
    Returns:
        Page: The main game page.
    """
    return Page(
        state,
        [
            Header("Ghost Hunt"),
            "Find all the ghosts by flipping tiles!",
            Button("New Game", "new_game"),
        ],
    )


@route
def new_game(state: State) -> Page:
    """
    Starts a new game by initializing the game state.

    Args:
        state (State): The current state of the game.
    Returns:
        Page: The game page with the new game state.
    """
    state.grid = make_ghost_grid(state.seed, state.size, state.ghosts)
    state.score = 0
    return play_game(state)


def make_tile_button(tile: Tile) -> Button:
    """
    Creates a button for a tile that can be flipped.

    Args:
        tile (Tile): The tile to create a button for.
    Returns:
        Button: A button that, when clicked, will flip the tile.
    """
    return Button(
        "",
        "flip_tile",
        arguments=[Argument("x", tile.x), Argument("y", tile.y)],
    )


def draw_grid(grid: list[list[Tile]]) -> list[list[PageContent]]:
    """
    Draws the game board grid, showing flipped tiles and buttons for unflipped tiles.

    Args:
        grid (list[list[Tile]]): The game board grid.
    Returns:
        list[list[PageContent]]: A grid representation where flipped tiles show their text
            and unflipped tiles are represented as buttons.
    """
    display = []
    for row in grid:
        display_row = []
        for tile in row:
            if tile.flipped:
                display_row.append(tile.text)
            else:
                display_row.append(make_tile_button(tile))
        display.append(display_row)
    return display


@route
def play_game(state: State) -> Page:
    """
    Plays the game by displaying the current state of the grid.

    Args:
        state (State): The current state of the game.
    Returns:
        Page: The game page showing the current grid.
    """
    grid_display = draw_grid(state.grid)
    return Page(
        state,
        [
            "Press a button to look for ghosts.",
            "Candy means a ghost is nearby!",
            Table(grid_display),
        ],
    )


@route
def flip_tile(state: State, x: int, y: int) -> Page:
    """
    Flips a tile at the specified coordinates and updates the game state.

    Args:
        state (State): The current state of the game.
        x (int): The x-coordinate of the tile to flip.
        y (int): The y-coordinate of the tile to flip.
    Returns:
        Page: The updated game page after flipping the tile.
    """
    tile = state.grid[y][x]
    tile.flipped = True
    if tile.text == GHOST:
        state.score += 1
    if state.score == state.ghosts:
        return game_won(state)
    return play_game(state)


@route
def game_won(state: State) -> Page:
    """
    Displays the game won page when all ghosts have been found.

    Args:
        state (State): The current state of the game.
    Returns:
        Page: The game won page.
    """
    return Page(
        state,
        [
            Header("You found all the ghosts!"),
            GHOST * state.ghosts,
            "Congratulations!",
            Button("Play Again", "new_game"),
        ],
    )


start_server(State([], 42, 0, 5, 3))
