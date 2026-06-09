class Response:
    """
    Response class to handle the response of the API

    Attributes:
        sucess (bool): The success of the response.
        data: The data of the response.
        error: The error of the response.

    Returns:
        Response: The response of the API.
    """

    def __init__(self, sucess: bool, data=None, error=None):
        self.sucess = sucess
        self.data = data
        self.error = error

    @classmethod
    def ok(cls, data):
        """
        Build a successful response wrapping the given payload.

        Args:
            data: The payload to return to the caller.

        Returns:
            Response: A response with ``sucess=True`` and ``data`` set.
        """
        return cls(sucess=True, data=data)

    @classmethod
    def fail(cls, error):
        """
        Build a failed response wrapping the given error.

        Args:
            error: The error description to return to the caller.

        Returns:
            Response: A response with ``sucess=False`` and ``error`` set.
        """
        return cls(sucess=False, error=error)
