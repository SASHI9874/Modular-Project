
from setuptools import setup, find_packages

setup(
    name="my_custom_ai_sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=['openpyxl>=3.1.2', 'pymupdf>=1.23.8', 'openai==1.3.0', 'python-docx>=1.1.0', 'httpx==0.27.2'],
    author="AI Platform User",
    description="A custom generated AI SDK",
)
