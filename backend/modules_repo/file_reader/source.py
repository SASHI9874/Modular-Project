# ai_platform/modules_repo/file_reader/source.py
import os

class FileReader:
    def __init__(self):
        pass

    def run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read() 
            print(f"File Read ({len(content)} chars)")
            return content