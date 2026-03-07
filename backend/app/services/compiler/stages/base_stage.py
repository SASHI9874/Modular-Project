from abc import ABC, abstractmethod

class BaseStage(ABC):
    @abstractmethod
    def run(self, context):
        pass