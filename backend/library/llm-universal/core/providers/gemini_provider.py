import logging
import os
from typing import List, Dict, Iterator
from google import genai
from google.genai import types

from .base import BaseLLMProvider, LLMResponse
from ..errors import AuthenticationError, RateLimitError, ProviderUnavailableError, LLMError, ContextWindowError

class GeminiProvider(BaseLLMProvider):
    def validate_config(self):
        if not os.getenv("GOOGLE_API_KEY") and "api_key" not in self.config:
            raise ValueError("Missing GOOGLE_API_KEY for Gemini Provider")

    def _clean_model_name(self, model: str) -> str:
        """Normalizes model aliases to avoid version-specific 404 errors."""
        if model.startswith("models/"):
            model = model.replace("models/", "", 1)

        # Some aliases (for example `*-latest`) are not available on all API versions.
        if model.endswith("-latest"):
            model = model[:-7]

        return model

    def _get_client(self):
        """Initialize Google Gemini client with new SDK."""
        api_key = self.config.get("api_key") or os.getenv("GOOGLE_API_KEY")
        api_version = self.config.get("api_version") or os.getenv("GOOGLE_API_VERSION", "v1")
        
        # Create client with explicit API version
        client = genai.Client(
            api_key=api_key
            # http_options={'api_version': api_version}
        )
        
        return client

    def _parse_messages(self, messages: List[Dict[str, str]]):
        """
        Splits messages into:
        1. System Instruction (if any)
        2. Chat History (list of Content objects)
        3. Last User Message (string)
        """
        system_instruction = None
        history = []
        last_user_message = ""

        # 1. Extract System Prompt first
        if messages and messages[0]["role"] == "system":
            system_instruction = messages[0]["content"]
            conversation_messages = messages[1:]
        else:
            conversation_messages = messages

        # 2. If it's a fresh chat, just return the last message
        if not conversation_messages:
            return system_instruction, [], ""

        # 3. Separate history from the final prompt
        # The last message is the new prompt we send to generate()
        last_msg = conversation_messages[-1]
        if last_msg["role"] == "user":
            last_user_message = last_msg["content"]
            history_msgs = conversation_messages[:-1]
        else:
            # Edge case: If the last message isn't user, treat it as history (rare)
            last_user_message = "Continue" 
            history_msgs = conversation_messages

        # 4. Convert history to Gemini format using new SDK types
        for msg in history_msgs:
            role = "user" if msg["role"] == "user" else "model"
            history.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])]
                )
            )

        return system_instruction, history, last_user_message

    def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        try:
            system_instruction, chat_history, user_message = self._parse_messages(messages)
            
            client = self._get_client()
            model_name = self._clean_model_name(self.config.get("model", "gemini-3-flash-preview"))
            
            # Build generation config WITHOUT system_instruction
            config = types.GenerateContentConfig(
                temperature=self.config.get("temperature", 0.7),
                max_output_tokens=self.config.get("max_tokens", 2000),
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
            
            # NEW: If there's a system instruction, prepend it to the first user message
            contents = chat_history.copy() if chat_history else []
            
            if system_instruction:
                # Combine system instruction with user message
                combined_message = f"{system_instruction}\n\n{user_message}"
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=combined_message)]
                    )
                )
            else:
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=user_message)]
                    )
                )
            
            # Generate content
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            
            # Token usage handling
            token_usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                token_usage = {
                    'prompt_tokens': getattr(usage, 'prompt_token_count', 0),
                    'completion_tokens': getattr(usage, 'candidates_token_count', 0),
                    'total_tokens': getattr(usage, 'total_token_count', 0)
                }
            
            return LLMResponse(
                content=response.text,
                token_usage=token_usage,
                raw_response=response
            )

        except Exception as e:
            error_str = str(e).lower()
            print("*"*100)
            print(str(e))
            print("*"*100)
            logging.exception(" error : ")
            
            # Map errors
            if "api key" in error_str or "401" in error_str or "unauthenticated" in error_str:
                raise AuthenticationError(str(e), "gemini")
            elif "invalid argument" in error_str or "400" in error_str:
                raise LLMError(f"Invalid request to Gemini API: {str(e)}", "gemini")
            elif "context" in error_str or "too long" in error_str:
                raise ContextWindowError(str(e), "gemini")
            elif "429" in error_str or "quota" in error_str:
                raise RateLimitError(str(e), "gemini")
            elif "503" in error_str or "unavailable" in error_str:
                raise ProviderUnavailableError(str(e), "gemini")
            elif "404" in error_str or "not found" in error_str:
                model_name = self.config.get("model", "gemini-1.5-flash")
                raise LLMError(
                    str(e),
                    "gemini"
                )
            else:
                raise LLMError(f"Gemini Error: {str(e)}", "gemini")

    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        try:
            system_instruction, chat_history, user_message = self._parse_messages(messages)
            
            client = self._get_client()
            model_name = self._clean_model_name(self.config.get("model", "gemini-1.5-flash"))
            
            # Build generation config
            config = types.GenerateContentConfig(
                temperature=self.config.get("temperature", 0.7),
                max_output_tokens=self.config.get("max_tokens", 2000),
                system_instruction=system_instruction if system_instruction else None,
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
            
            # Prepare contents
            contents = chat_history.copy() if chat_history else []
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_message)]
                )
            )
            
            # Stream response with new SDK
            response_stream = client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config
            )
            
            for chunk in response_stream:
                # SAFETY CHECK: Accessing .text raises error if content was blocked
                try:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
                except (ValueError, AttributeError):
                    # Content blocked by safety filters - skip this chunk
                    continue

        except Exception as e:
            error_str = str(e).lower()
            
            if "api key" in error_str or "401" in error_str:
                raise AuthenticationError(str(e), "gemini")
            elif "429" in error_str or "quota" in error_str:
                raise RateLimitError(str(e), "gemini")
            elif "503" in error_str or "unavailable" in error_str:
                raise ProviderUnavailableError(str(e), "gemini")
            elif "404" in error_str or "not found" in error_str:
                model_name = self.config.get("model", "gemini-1.5-flash")
                raise LLMError(
                    f"Model '{model_name}' not found during streaming. "
                    f"Try: gemini-1.5-flash (without 'models/' prefix)",
                    "gemini"
                )
            else:
                raise LLMError(f"Gemini Streaming Error: {str(e)}", "gemini")
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for Google Gemini.
        Gemini 1.5 Flash is free up to 15 requests/min, 1500 requests/day
        After that: $0.075 per 1M input tokens, $0.30 per 1M output tokens
        """
        model = self.config.get("model", "gemini-1.5-flash")
        
        # Pricing per 1M tokens (as of 2024-2025)
        if "1.5-flash" in model or "2.0-flash" in model:
            # Flash models
            input_cost_per_million = 0.075
            output_cost_per_million = 0.30
        elif "1.5-pro" in model:
            # Pro models (more expensive)
            input_cost_per_million = 1.25
            output_cost_per_million = 5.00
        else:
            # Conservative estimate
            input_cost_per_million = 0.075
            output_cost_per_million = 0.30
        
        cost = (
            (input_tokens / 1_000_000 * input_cost_per_million) +
            (output_tokens / 1_000_000 * output_cost_per_million)
        )
        
        return round(cost, 6)
