"""
    Helper functions used in debate strategies.
"""
from metrics import extract_time_complexity

def get_set_number_solutions(placeholder, AGENTS_NO):
    """
        Returns a list of agent indices excluding the one specified by `placeholder`.

        Parameters:
        - placeholder (int): Index of the agent to exclude.
        - AGENTS_NO (int): Total number of agents.

        Used to identify all other agents except the current one, useful for peer evaluation.
    """

    list_local = [None] * AGENTS_NO

    for i in range(0, AGENTS_NO):
        list_local[i] = i

    for var in list_local:
        if(var == int(placeholder)):
            list_local.remove(var)
            break

    return list_local


def remove_duplicates(list_local):
    """
        Removes duplicate elements from a list while preserving order.

        Parameters:
        - list_local (List): List containing potential duplicates.

        Returns:
        - List with unique elements in the original order of appearance.
    """

    result = []
    explored = set()
    for element in list_local:
        if element not in explored:
            result.append(element)
            explored.add(element)
    return result


def equals_time_complexity(solutions):
    """
        Checks whether all given solutions have the same time complexity.

        Parameters:
        - solutions (List[str]): List of solution code snippets or descriptors.

        Returns:
        - True if all time complexities are identical, False otherwise.

        Internally uses `extract_time_complexity()` to analyze each solution.
    """

    list_local = []
    for var in solutions:
        list_local.append(extract_time_complexity(var))
    print("Complessità di tempo estratte: ")
    print(list_local)
    set_local = set(list_local)
    if len(set_local) == 1:
        return True
    else:
        return False


def equals_cognitive_complexity(cognitive_complexity_sol):
    """
        Checks if all cognitive complexity scores are equal across solutions.

        Parameters:
        - cognitive_complexity_sol (List[int]): List of complexity scores for each solution.

        Returns:
        - True if all scores are the same, False otherwise.
    """

    set_local = set(cognitive_complexity_sol)
    if len(set_local) == 1:
        return True
    else:
        return False


def get_random_element(list_local):
    """
        Randomly selects and returns an element from a list.

        Parameters:
        - list_local (List): List of items to choose from.

        Returns:
        - A randomly selected element, or None if the list is empty.

        Useful when multiple equally valid solutions exist and a tie-breaker is needed.
    """
    import random

    if not list_local:
        return None
    return random.choice(list_local)
