import hashlib
import inspect


class BaseStrategy:
    def __init__(
        self,
        strategy_name=None,
        strategy_description=None,
        strategy_name_slug=None,
        strategy_version="0.0.1",
        variable_basic_points=1,
        variable_bonus_points=1,
    ):
        self.debug = False
        self.strategy_name = strategy_name
        self.strategy_description = strategy_description
        self.strategy_name_slug = strategy_name_slug
        self.strategy_version = strategy_version
        self.variable_basic_points = variable_basic_points
        self.variable_bonus_points = variable_bonus_points
        self.hash_version = self._generate_hash_of_calculate_points()

    def _generate_hash_of_calculate_points(self):
        source_code = inspect.getsource(self.calculate_points)
        hash_object = hashlib.sha256(source_code.encode())
        return hash_object.hexdigest()

    def debug_print(self, *args):
        if self.debug:
            print("\033[95m", *args, "\033[0m")

    def get_strategy_id(self):
        # get filename of this file
        return self.__class__.__name__

    def get_strategy_name(self):
        return self.strategy_name

    def get_strategy_description(self):
        return self.strategy_description

    def get_strategy_name_slug(self):
        return self.strategy_name_slug

    def get_strategy_version(self):
        return self.strategy_version

    def get_variable_basic_points(self):
        return self.variable_basic_points

    def get_variable_bonus_points(self):  # noqa
        return self.variable_bonus_points

    def set_variables(self, new_variables):  # noqa
        variables_changed = []
        for new_variable, new_value in new_variables.items():
            if hasattr(self, new_variable):
                setattr(self, new_variable, new_value)
                variables_changed.append(new_variable)
        return variables_changed

    def get_variables(self):
        return {k: v for k, v in self.__dict__.items() if
                k.startswith("variable_")}

    def get_variable(self, variable_name):  # noqa
        if hasattr(self, variable_name):
            return getattr(self, variable_name)
        return None

    def set_variable(self, variable_name, variable_value):  # noqa
        if hasattr(self, variable_name):
            setattr(self, variable_name, variable_value)
            return True
        return False

    def get_strategy(self):  # noqa
        return {
            "name": self.get_strategy_name(),
            "description": self.get_strategy_description(),
            "name_slug": self.get_strategy_name_slug(),
            "version": self.get_strategy_version(),
            "variables": self.get_variables(),
            "calculate_points_hash": self.hash_version,
        }

    def calculate_points(self):
        return self.get_variable_basic_points()
