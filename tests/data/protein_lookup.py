from dataclasses import dataclass
from drafter import *

# The path to the food data file.
FOOD_DATA_FILE = "food_simple.tsv"


@dataclass
class State:
    """
    Represents the state of the food lookup application.

    Attributes:
        food_items (list[int]): A list of food item IDs that the user has selected.
    """

    food_items: list[int]


@dataclass
class Food:
    """
    Represents a food item with its details.

    Attributes:
        category (str): The category of the food item.
        name (str): The name of the food item.
        id (int): The unique identifier of the food item.
        protein (float): The protein content of the food item in grams.
    """

    category: str
    name: str
    id: int
    protein: float


def parse_food(line: str) -> Food:
    """
    Parses a line from the food_simple.tsv file and returns a Food object.

    Args:
        line (str): A line from the food_simple.tsv file.
    Returns:
        Food: A Food object with the parsed details.
    """
    pieces = line.strip().split("\t")
    category = pieces[0]
    name = pieces[1]
    food_id = int(pieces[2])
    protein = float(pieces[3])
    return Food(category, name, food_id, protein)


def load_foods() -> list[Food]:
    """
    Loads food items from the food_simple.tsv file.

    Returns:
        list[Food]: A list of Food objects loaded from the file.
    """
    food_items = []
    with open(FOOD_DATA_FILE) as file:
        for line in file:
            food_items.append(parse_food(line))
    return food_items


# Load the food items once at the start of the program.
FOODS = load_foods()


def find_foods(foods: list[Food], query: str) -> list[Food]:
    """
    Finds food items that match the given query. Ignores capitalization.
    As long as the query is a substring of the food name, it is considered a match.

    Args:
        foods (list[Food]): A list of Food objects to search.
        query (str): The search query string.
    Returns:
        list[Food]: A list of Food objects that match the query.
    """
    results = []
    query_lower = query.lower()
    for food in foods:
        if query_lower in food.name.lower():
            results.append(food)
    return results


def get_food(foods: list[Food], food_ids: list[int]) -> list[Food]:
    """
    Retrieves food items that match the given list of food IDs.

    Args:
        foods (list[Food]): A list of Food objects to search.
        food_ids (list[int]): A list of food IDs to look for.
    Returns:
        list[Food]: A list of Food objects that match the given food IDs.
    """
    selected_foods = []
    for food in foods:
        if food.id in food_ids:
            selected_foods.append(food)
    return selected_foods


@route
def index(state: State):
    """
    The main page of the food lookup application, where users can search for foods
    and see their protein content. Also lists the foods the user has selected, and
    shows the total protein content of those foods.

    Args:
        state (State): The current state of the application.
    Returns:
        Page: The main page of the application.
    """
    selected_foods = get_food(FOODS, state.food_items)
    total_protein_value = total_protein(selected_foods)
    return Page(
        state,
        [
            Header("Food Lookup"),
            "Find foods by name and see their protein content.",
            TextBox("query"),
            Button("Search", "search"),
            Table(selected_foods),
            "Total protein:",
            str(total_protein_value),
        ],
    )


def total_protein(foods: list[Food]) -> float:
    """
    Calculates the total protein content of a list of food items.

    Args:
        foods (list[Food]): A list of Food objects.
    Returns:
        float: The total protein content of the food items.
    """
    total = 0.0
    for food in foods:
        total += food.protein
    return total


def no_food_found_page(state: State) -> Page:
    """
    Displays a page indicating that no food items were found for the given search query.

    Args:
        state (State): The current state of the application.
    Returns:
        Page: A page indicating that no food items were found.
    """
    return Page(
        state,
        [
            Header("No results found"),
            "Try a different search term.",
            Button("Back", "index"),
        ],
    )


def make_food_button(food: Food) -> PageContent:
    """
    Creates a button for a food item that can be added to the user's selected foods.
    Also shows the category and protein content of the food item.

    Args:
        food (Food): The food item to create a button for.
    Returns:
        Button: A button that, when clicked, will add the food item to the user's selected foods.
    """
    return Row(
        Button(food.name, "add_food", arguments=[Argument("food_id", food.id)]),
        food.category + " - " + str(food.protein) + "g protein",
    )


@route
def search(state: State, query: str):
    """
    Searches for food items that match the given query and displays the results.
    If no results are found, an error message is displayed.

    Args:
        state (State): The current state of the application.
        query (str): The search query string.
    Returns:
        Page: A page displaying the search results or an error message.
    """
    results = find_foods(FOODS, query)
    if not results:
        return no_food_found_page(state)
    buttons = []
    for food in results:
        buttons.append(make_food_button(food))
    return Page(
        state,
        [
            Header(f"Search results for '{query}'"),
            BulletedList(buttons),
            Button("Back", "index"),
        ],
    )


@route
def add_food(state: State, food_id: int):
    """
    Adds a food item to the user's selected foods.

    Args:
        state (State): The current state of the application.
        food_id (int): The ID of the food item to add.
    Returns:
        Page: The main page of the application with the updated selected foods.
    """
    if food_id not in state.food_items:
        state.food_items.append(food_id)

    return index(state)


start_server(State([]))
