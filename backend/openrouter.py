"""OpenRouter API client for making LLM requests."""

import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional, Tuple
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL

logger = logging.getLogger(__name__)


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not configured")
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            # Safe response parsing with validation
            choices = data.get('choices')
            if not choices or len(choices) == 0:
                logger.error(f"Model {model} returned empty choices")
                return None

            message = choices[0].get('message')
            if not message:
                logger.error(f"Model {model} returned no message in choice")
                return None

            content = message.get('content')
            if not content:
                logger.warning(f"Model {model} returned empty content")

            return {
                'content': content or '',
                'reasoning_details': message.get('reasoning_details')
            }

    except httpx.TimeoutException:
        logger.error(f"Timeout querying model {model} after {timeout}s")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error querying model {model}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Error querying model {model}: {type(e).__name__}")
        return None


async def query_executive(
    role_key: str,
    model: str,
    system_prompt: str,
    user_query: str,
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a model with an executive persona.

    Args:
        role_key: Executive role identifier (CEO, CFO, etc.)
        model: OpenRouter model identifier
        system_prompt: The executive persona/system prompt
        user_query: The user's question/situation
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content', or None if failed
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]

    return await query_model(model, messages, timeout)


async def query_executives_parallel(
    executives: Dict[str, Dict[str, str]],
    user_query: str
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query all executive roles in true parallel using asyncio.gather.

    Args:
        executives: Dict mapping role_key to {'model': ..., 'persona': ...}
        user_query: The user's question/situation

    Returns:
        Dict mapping role_key to response dict (or None if failed)
    """
    async def query_one(role_key: str, config: Dict[str, str]) -> Tuple[str, Optional[Dict[str, Any]]]:
        result = await query_executive(
            role_key,
            config['model'],
            config['persona'],
            user_query
        )
        return role_key, result

    # Create all query tasks
    tasks = [query_one(role_key, config) for role_key, config in executives.items()]

    # Execute ALL tasks in true parallel with asyncio.gather
    # return_exceptions=True prevents one failure from cancelling others
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert results to dict, handling any exceptions
    results = {}
    for item in results_list:
        if isinstance(item, Exception):
            logger.error(f"Executive query failed with exception: {type(item).__name__}")
            continue
        role_key, result = item
        results[role_key] = result

    return results
