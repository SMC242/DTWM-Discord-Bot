"""A class for sharing data between all subclasses"""

class Borg:
    """
    Class for sharing data between all subclasses
    
    ATTRIBUTES
    data: dict
        The data to share between all subclasses.
    """

    def __init__(self, data: dict):
        """
        ARGUMENTS
        data:
            The data to share between all subclasses.
        """

        self.data = data