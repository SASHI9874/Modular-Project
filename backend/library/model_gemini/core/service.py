from typing import List, Dict, Any
from google import genai
from google.genai import types

def generate_chat_completion(
    messages: List[Dict[str, str]],
    api_key: str,
    model_name: str = "gemini-3-flash-preview",
    temperature: float = 0.7
) -> str:
    """
    Pure business logic for calling the Google Gemini API using the new SDK.
    """
    if not api_key:
        raise ValueError("Gemini API key is required.")

    # 1. Initialize Client
    client = genai.Client(api_key=api_key)

    # 2. Parse Messages (Your exact logic)
    system_instruction = None
    if messages and messages[0]["role"] == "system":
        system_instruction = messages[0]["content"]
        conversation_messages = messages[1:]
    else:
        conversation_messages = messages

    if not conversation_messages:
        return ""

    last_msg = conversation_messages[-1]
    if last_msg["role"] == "user":
        last_user_message = last_msg["content"]
        history_msgs = conversation_messages[:-1]
    else:
        last_user_message = "Continue" 
        history_msgs = conversation_messages

    contents = []
    for msg in history_msgs:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            )
        )

    # Prepend system instruction to the final user message
    if system_instruction:
        combined_message = f"{system_instruction}\n\n{last_user_message}"
        contents.append(
            types.Content(role="user", parts=[types.Part(text=combined_message)])
        )
    else:
        contents.append(
            types.Content(role="user", parts=[types.Part(text=last_user_message)])
        )

    # 3. Build Config (Your exact safety settings)
    config = types.GenerateContentConfig(
        temperature=temperature,
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_ONLY_HIGH"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_ONLY_HIGH"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_ONLY_HIGH"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_ONLY_HIGH"
            ),
        ]
    )

    # 4. Generate Content
    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config
    )

    return response.text