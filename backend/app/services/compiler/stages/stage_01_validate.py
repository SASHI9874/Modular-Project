from .base_stage import BaseStage
class ValidationStage(BaseStage):
    def run(self, context):
        print("Validating Graph...")