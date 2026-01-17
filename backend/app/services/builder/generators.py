from typing import List, Dict

class CodeGenerator:
    @staticmethod
    def generate_setup_py(package_name: str, requirements: List[str]) -> str:
        # (This method remains unchanged)
        return f"""
from setuptools import setup, find_packages

setup(
    name="{package_name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires={requirements},
    author="AI Platform User",
    description="A custom generated AI SDK",
)
"""

    @staticmethod
    def generate_main_py(features_meta: List[Dict], package_name: str) -> str:
        """
        Generates main.py dynamically using the 'class_name' from meta.json.
        """
        imports = []
        steps = []
        
        for meta in features_meta:
            feature_id = meta.get("id") # The folder name/ID
            class_name = meta.get("class_name", "UnknownClass")
            nice_name = meta.get("name", feature_id)
            
            # 1. Dynamic Import
            # "from my_custom_ai_sdk.file_reader import FileReader"
            imports.append(f"from {package_name}.{feature_id} import {class_name}")

            # 2. Dynamic Execution Step
            steps.append(f"    # Step: {nice_name}")
            
            # FUTURE PROOFING: 
            # If you add "env_vars": ["OPENAI_API_KEY"] to meta.json later, 
            # this logic will automatically handle it.
            if "env_vars" in meta and meta["env_vars"]:
                env_args = ", ".join([f"{k}=os.getenv('{k}', '')" for k in meta["env_vars"]])
                steps.append(f"    processor = {class_name}({env_args})")
            else:
                steps.append(f"    processor = {class_name}()")
                
            steps.append(f"    data = processor.run(data)")

        return f"""
import sys
import os
{chr(10).join(imports)}

def main():
    print("🚀 Starting AI Pipeline...")
    
    if len(sys.argv) > 1:
        data = sys.argv[1] # Take from command line
    else:
        data = input("Enter input (File Path or Text): ")

    print(f"Input: {{data}}")

    try:
{chr(10).join(steps)}
        print("-" * 20)
        print("✅ Final Output:")
        print(data)
    except Exception as e:
        print(f"❌ Error during execution: {{e}}")

if __name__ == "__main__":
    main()
"""