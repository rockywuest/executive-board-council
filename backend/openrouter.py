"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


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
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
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
    Query all executive roles in parallel.

    Args:
        executives: Dict mapping role_key to {'model': ..., 'persona': ...}
        user_query: The user's question/situation

    Returns:
        Dict mapping role_key to response dict (or None if failed)
    """
    import asyncio

    async def query_one(role_key: str, config: Dict[str, str]):
        return await query_executive(
            role_key,
            config['model'],
            config['persona'],
            user_query
        )

    # Create tasks for all executives
    tasks = {
        role_key: asyncio.create_task(query_one(role_key, config))
        for role_key, config in executives.items()
    }

    # Wait for all to complete
    results = {}
    for role_key, task in tasks.items():
        results[role_key] = await task

    return results
