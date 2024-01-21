

class VariableBase():

    def __init__(self, variable_name, variable_description, sub_variables):
        self.variable_name = variable_name
        self.variable_description = variable_description
        self.sub_variables = sub_variables

    def get_data(self):
        return {
            "name": self.variable_name,
            "description": self.variable_description,
            "sub_variables": self.sub_variables
        }
