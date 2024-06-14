def singleton(class_):
    """
    Decorator function to create a singleton class.

    Args:
        class_ (type): The class to be converted into a singleton.

    Returns:
        function: The inner function that manages the single instance.
    """
    instances = {}

    def getinstance(*args, **kwargs):
        """
        Retrieves the single instance of the class, creating it if necessary.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            object: The single instance of the class.
        """
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance
