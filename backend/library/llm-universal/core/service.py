from typing import Dict, Any, Optional, Iterator
import time
from .factory import get_llm_provider
from .config import LLMConfig
from .utils import with_retries, with_stream_retry, count_tokens
from .errors import LLMError, ContextWindowError

# Get config once
RETRY_CONF = LLMConfig.get_retry_config()

@with_retries(
    max_attempts=RETRY_CONF["max_attempts"],
    min_seconds=RETRY_CONF["min_seconds"],
    max_seconds=RETRY_CONF["max_seconds"]
)
def _execute_chat(provider_config: Dict[str, Any], messages: list) -> tuple:
    """
    Internal function to execute the chat with metrics tracking.
    Returns (content, token_usage, elapsed_time)
    """
    start_time = time.time()
    
    # 1. Validate token limits BEFORE calling provider
    token_count = count_tokens(messages, provider_config.get("model", "gpt-4"))
    max_context = provider_config.get("max_tokens", 4096) * 2  # Rough context window estimate
    
    if token_count > max_context:
        raise ContextWindowError(
            f"Prompt too long: {token_count} tokens exceeds estimated limit of {max_context}",
            provider_config["provider"]
        )
    
    # 2. Initialize Provider
    llm = get_llm_provider(provider_config)
    
    # 3. Execute
    response = llm.chat(messages)
    
    # 4. Calculate metrics
    elapsed = time.time() - start_time
    
    # 5. Log metrics
    print(f"   [LLM Metrics]")
    print(f"   Provider: {provider_config['provider']}")
    print(f"   Model: {provider_config.get('model', 'default')}")
    print(f"   Input Tokens: ~{token_count}")
    print(f"   Output Tokens: {response.token_usage.get('completion_tokens', 'N/A')}")
    print(f"   Total Tokens: {response.token_usage.get('total_tokens', 'N/A')}")
    print(f"   Latency: {elapsed:.2f}s")
    
    # Estimate cost if provider supports it
    try:
        input_tokens = response.token_usage.get('prompt_tokens', token_count)
        output_tokens = response.token_usage.get('completion_tokens', 0)
        cost = llm.estimate_cost(input_tokens, output_tokens)
        print(f"   Estimated Cost: ${cost:.6f}")
    except:
        pass  # Cost estimation not available for this provider
    
    return response.content, response.token_usage, elapsed


def chat(prompt: str, context: str = "", override_config: Optional[Dict] = None) -> str:
    """
    Universal Chat Function with Retries, Validation, and Metrics.
    
    Args:
        prompt: User's question/instruction
        context: Optional context for RAG (if from retriever/PDF)
        override_config: Optional config overrides (e.g., from UI)
    
    Returns:
        AI response as string
    """
    try:
        # 1. Load Config (Env > Defaults > Overrides)
        config = LLMConfig.get_provider_config()
        if override_config:
            config.update(override_config)

        # 2. Build Messages (RAG Logic)
        messages = []
        
        if context:
            # RAG MODE: Include context in system message
            system_prompt = (
                "You are a helpful AI assistant. "
                "Use the following context to answer the user's question accurately. "
                "If the answer is not in the context, say so.\n\n"
                f"Context:\n{context}"
            )
            messages.append({"role": "system", "content": system_prompt})
        else:
            # STANDARD MODE
            messages.append({"role": "system", "content": "You are a helpful AI assistant."})
            
        messages.append({"role": "user", "content": prompt})

        # 3. Execute with Retries and Metrics
        content, token_usage, elapsed = _execute_chat(config, messages)
        return content

    except LLMError as e:
        # Known Provider Error with clear message
        return f" AI Provider Error: {str(e)}"
    
    except Exception as e:
        # Unknown System Error - log for debugging
        import traceback
        print(f" [LLM Service] Unexpected Error:")
        print(traceback.format_exc())
        return f" System Error: {str(e)}"


@with_stream_retry(max_attempts=3)
def stream_chat(prompt: str, context: str = "", override_config: Optional[Dict] = None) -> Iterator[str]:
    """
    Generator function for Streaming Chat with connection retry.
    Yields chunks of text (tokens) as they are generated.
    
    Note: Retries only the initial connection, not mid-stream errors.
    """
    try:
        # 1. Load Config
        config = LLMConfig.get_provider_config()
        if override_config:
            config.update(override_config)
        
        # 2. Validate token limits
        messages = []
        if context:
            messages.append({
                "role": "system", 
                "content": f"Use this context to answer:\n\n{context}"
            })
        else:
            messages.append({"role": "system", "content": "You are a helpful assistant."})
        
        messages.append({"role": "user", "content": prompt})
        
        # Check token count
        token_count = count_tokens(messages, config.get("model", "gpt-4"))
        max_context = config.get("max_tokens", 4096) * 2
        
        if token_count > max_context:
            yield f"[ERROR: Prompt too long ({token_count} tokens)]"
            return
        
        # 3. Initialize Provider
        llm = get_llm_provider(config)
        
        # 4. Stream Response
        print(f" [LLM Streaming] Provider: {config['provider']}, Model: {config.get('model')}")
        
        for chunk in llm.stream(messages):
            yield chunk

    except LLMError as e:
        yield f"[ERROR: {str(e)}]"
    
    except Exception as e:
        import traceback
        print(f" [LLM Streaming] Error:")
        print(traceback.format_exc())
        yield f"[ERROR: {str(e)}]"