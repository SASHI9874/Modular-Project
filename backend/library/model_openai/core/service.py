from typing import List, Dict
from openai import OpenAI

def generate_chat_completion(
    messages: List[Dict[str, str]],
    api_key: str,
    model_name: str = "gpt-4o",
    temperature: float = 0.7
) -> str:
    """
    Pure business logic for calling the OpenAI Chat Completions API.
    Has zero knowledge of the workflow engine or canvas context.
    """
    if not api_key:
        raise ValueError("OpenAI API key is required.")

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature
    )

    return response.choices[0].message.content