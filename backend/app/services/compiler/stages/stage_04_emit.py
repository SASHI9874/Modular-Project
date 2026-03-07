from .base_stage import BaseStage
class CodeEmissionStage(BaseStage):
    def run(self, context):
        print("Generating Python Code...")