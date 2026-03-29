import time
import functools
import random
from typing import Callable, List, Dict, Iterator
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from .errors import RateLimitError, ProviderUnavailableError

def convert_to_langchain_messages(messages: List[Dict[str, str]]):
    """
    Convert standard message dicts to LangChain message objects.
    This is the single source of truth for message conversion.
    """
    lc_messages = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "system":
            lc_messages.append(SystemMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        else:
            # Default to user message for unknown roles
            lc_messages.append(HumanMessage(content=content))
    
    return lc_messages


def with_retries(max_attempts: int = 3, min_seconds: int = 1, max_seconds: int = 10):
    """
    Decorator to retry functions on transient errors (Rate Limits, 503s).
    Uses 'Exponential Backoff with Jitter'.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            last_error = None
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                
                except (RateLimitError, ProviderUnavailableError) as e:
                    last_error = e
                    if attempt == max_attempts:
                        raise e  # Give up
                    
                    # Exponential Backoff: 2^attempt (2s, 4s, 8s...)
                    sleep_time = min(max_seconds, min_seconds * (2 ** (attempt - 1)))
                    
                    # Jitter: Add random noise to prevent "Thundering Herd" problem
                    sleep_time += random.uniform(0, 1)
                    
                    print(f" [LLM Retry] Attempt {attempt}/{max_attempts} failed: {str(e)}. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    attempt += 1
                
                except Exception as e:
                    # Don't retry unknown errors or Auth errors
                    raise e
            
            # This should never be reached, but just in case
            raise last_error
                    
        return wrapper
    return decorator


def with_stream_retry(max_attempts: int = 3):
    """
    Retry only the stream connection, not mid-stream chunks.
    Once streaming starts, we don't retry (too complex).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            last_error = None
            
            while attempt <= max_attempts:
                try:
                    # Return the generator directly - don't iterate here
                    # This only retries the initial connection
                    return func(*args, **kwargs)
                    
                except (RateLimitError, ProviderUnavailableError) as e:
                    last_error = e
                    if attempt == max_attempts:
                        raise e
                    
                    sleep_time = min(10, 2 ** (attempt - 1))
                    print(f" [Stream Retry] Attempt {attempt}/{max_attempts} failed. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    attempt += 1
                
                except Exception as e:
                    # Don't retry auth errors or unknown errors
                    raise e
            
            raise last_error
                    
        return wrapper
    return decorator


def count_tokens(messages: List[Dict[str, str]], model: str = "gpt-4") -> int:
    """
    Estimate token count for messages.
    Uses tiktoken for accurate counting.
    """
    try:
        import tiktoken
        
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to default encoding
            encoding = tiktoken.get_encoding("cl100k_base")
        
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # Message formatting tokens
            content = message.get("content", "")
            num_tokens += len(encoding.encode(content))
        
        num_tokens += 2  # Reply priming tokens
        return num_tokens
        
    except ImportError:
        # If tiktoken not installed, use rough estimate
        # Approximate: 1 token ≈ 4 characters
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4