# Gamification strategy using Getis-Ord Gi* statistic to identify hotspots in spatial
import hashlib
import inspect
from typing import Iterable

import numpy as np
from graphviz import Digraph


def _build_rook_weights(rows: int, cols: int) -> np.ndarray:
    """
    Build a rook-contiguity weights matrix (including self-neighbors).

    Each cell is connected to itself and to direct neighbors
    (up, down, left, right) when they exist.
    """
    n = rows * cols
    weights = np.zeros((n, n), dtype=float)

    def idx(r: int, c: int) -> int:
        return r * cols + c

    for r in range(rows):
        for c in range(cols):
            i = idx(r, c)
            weights[i, i] = 1.0
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < rows and 0 <= nc < cols:
                    weights[i, idx(nr, nc)] = 1.0
    return weights


def compute_getis_ord_gi_star(grid: Iterable[Iterable[float]]) -> np.ndarray:
    """
    Compute Getis-Ord Gi* z-scores for a 2D numeric grid.

    This implementation uses rook adjacency and includes the focal cell in the
    local neighborhood. It returns a matrix with one Gi* score per cell.
    """
    array = np.asarray(grid, dtype=float)
    if array.ndim != 2:
        raise ValueError("grid must be a 2D structure")

    rows, cols = array.shape
    x = array.reshape(-1)
    n = x.size
    if n < 2:
        return np.zeros_like(array, dtype=float)

    mean_x = np.mean(x)
    # Population standard deviation term used in classical Gi* implementation.
    std_x = np.sqrt((np.sum(x * x) / n) - (mean_x**2))
    if std_x == 0:
        return np.zeros_like(array, dtype=float)

    weights = _build_rook_weights(rows, cols)
    scores = np.zeros(n, dtype=float)

    for i in range(n):
        w_i = weights[i]
        sum_w = np.sum(w_i)
        sum_w_sq = np.sum(w_i * w_i)
        numerator = np.sum(w_i * x) - (mean_x * sum_w)
        denom_term = ((n * sum_w_sq) - (sum_w**2)) / (n - 1)
        denominator = std_x * np.sqrt(max(denom_term, 0.0))
        scores[i] = 0.0 if denominator == 0 else numerator / denominator

    return scores.reshape(rows, cols)


def rank_hotspots(grid: Iterable[Iterable[float]]) -> list[tuple[tuple[int, int], float]]:
    """
    Rank cells by Gi* score from strongest hotspot to weakest.
    """
    scores = compute_getis_ord_gi_star(grid)
    ranked = [((r, c), float(scores[r, c])) for r in range(scores.shape[0]) for c in range(scores.shape[1])]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked


class GetisOrdStrategy:

    def __init__(
        self,
        strategy_name="GeoEquityGamificationModel",
        strategy_description="GeoEquity Gamification Model - Based on Getis-Ord Gi*"
        "statistic to identify hotspots in spatial data.",
        strategy_name_slug="geo_equity_gamification_model",
        strategy_version="0.0.1",
        variable_basic_points=10,
        variable_bonus_points=10,
        variable_minutes_decay_per_polygon=0,
    ):
        """
        Initializes the BaseStrategy with the provided attributes.

        Args:
            strategy_name (str, optional): The name of the strategy.
            strategy_description (str, optional): A description of the
              strategy.
            strategy_name_slug (str, optional): A slugified version of the
              strategy name.
            strategy_version (str, optional): The version of the strategy.
              Default is "0.0.1".
            variable_basic_points (int, optional): The basic points variable
              for the strategy. Default is 1.
            variable_bonus_points (int, optional): The bonus points variable
              for the strategy. Default is 1.
        """
        self.debug = False
        self.strategy_name = strategy_name
        self.strategy_description = strategy_description
        self.strategy_name_slug = strategy_name_slug
        self.strategy_version = strategy_version
        self.variable_basic_points = variable_basic_points
        self.variable_bonus_points = variable_bonus_points
        self.hash_version = self._generate_hash_of_calculate_points()

    def _generate_hash_of_calculate_points(self):
        """
        Generates a SHA-256 hash of the source code of the calculate_points
          method. This hash is used for versioning the strategy.

        Returns:
            str: The SHA-256 hash of the calculate_points method.
        """
        source_code = inspect.getsource(self.calculate_points)
        hash_object = hashlib.sha256(source_code.encode())
        return hash_object.hexdigest()

    def debug_print(self, *args):
        """
        Prints debug information if debug mode is enabled.

        Args:
            *args: The arguments to print.
        """
        if self.debug:
            print("\033[95m", *args, "\033[0m")

    def get_strategy_id(self):
        """
        Retrieves the strategy ID, which is the class name. This id is the
          filename of the strategy.

        Returns:
            str: The strategy ID.
        """
        return self.__class__.__name__

    def get_strategy_name(self):
        """
        Retrieves the strategy name.

        Returns:
            str: The strategy name.
        """
        return self.strategy_name

    def get_strategy_description(self):
        """
        Retrieves the strategy description.

        Returns:
            str: The strategy description.
        """
        return self.strategy_description

    def get_strategy_name_slug(self):
        """
        Retrieves the slugified strategy name.

        Returns:
            str: The slugified strategy name.
        """
        return self.strategy_name_slug

    def get_strategy_version(self):
        """
        Retrieves the strategy version.

        Returns:
            str: The strategy version.
        """
        return self.strategy_version

    def get_variable_basic_points(self):
        """
        Retrieves the basic points variable.

        Returns:
            int: The basic points variable.
        """
        return self.variable_basic_points

    def get_variable_bonus_points(self):
        """
        Retrieves the bonus points variable.

        Returns:
            int: The bonus points variable.
        """
        return self.variable_bonus_points

    def set_variables(self, new_variables):
        """
        Sets multiple variables at once.

        Args:
            new_variables (dict): A dictionary of variable names and values.

        Returns:
            list: A list of variable names that were changed.
        """
        variables_changed = []
        for new_variable, new_value in new_variables.items():
            if hasattr(self, new_variable):
                setattr(self, new_variable, new_value)
                variables_changed.append(new_variable)
        return variables_changed

    def get_variables(self):
        """
        Retrieves all variables that start with 'variable_'.

        Returns:
            dict: A dictionary of variable names and their values.
        """
        return {k: v for k, v in self.__dict__.items() if k.startswith("variable_")}

    def get_variable(self, variable_name):
        """
        Retrieves the value of a specific variable.

        Args:
            variable_name (str): The name of the variable.

        Returns:
            The value of the variable if it exists, otherwise None.
        """
        if hasattr(self, variable_name):
            return getattr(self, variable_name)
        return None

    def set_variable(self, variable_name, variable_value):
        """
        Sets the value of a specific variable.

        Args:
            variable_name (str): The name of the variable.
            variable_value: The new value of the variable.

        Returns:
            bool: True if the variable was set, otherwise False.
        """
        if hasattr(self, variable_name):
            setattr(self, variable_name, variable_value)
            return True
        return False

    def get_strategy(self):
        """
        Retrieves the strategy details including name, description, slug,
          version, and variables.

        Returns:
            dict: A dictionary containing the strategy details.
        """
        return {
            "name": self.get_strategy_name(),
            "description": self.get_strategy_description(),
            "name_slug": self.get_strategy_name_slug(),
            "version": self.get_strategy_version(),
            "variables": self.get_variables(),
            "hash_version": self.hash_version,
        }

    async def calculate_points(self, data=None):
        """
        Calculates the points for the strategy.

        Returns:
            int: The basic points variable.
        """
        return self.get_variable_basic_points()

    def simulate_strategy(self, data=None):
        """
        Simulates the strategy for testing purposes.

        Returns:
            dict: A dictionary containing the simulated points.
        """
        return None

    def generate_logic_graph(self, format="png"):
        """
        Generates a logic graph for the strategy.

        Returns:
            str: The logic graph as a string.
        """
        dot = Digraph(comment="Points Calculation Logic", format=format)
        dot.node("A", "No logic graph available")
        return dot
