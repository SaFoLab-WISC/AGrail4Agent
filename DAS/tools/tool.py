from abc import ABC, abstractmethod

class Tools(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_checking_result(self, **kwargs):
        """
        This method must be implemented in a subclass.
        Should return two string variable: your tools checking result and your tool checking process.
        """
        pass





