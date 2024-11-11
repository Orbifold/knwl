from datetime import datetime

from typing import List

import ollama

from .jsonStorage import JsonStorage
from .settings import settings
from .utils import hash_args

# os.environ["TOKENIZERS_PARALLELISM"] = "false"

# note that LangChain has a ton of caching mechanisms in place: https://python.langchain.com/docs/integrations/llm_caching
ollama_cache = JsonStorage(namespace="ollama", cache=settings.cache_ollama)

ollama_client = ollama.AsyncClient()


async def is_in_cache(messages: str | List[str]):
    if isinstance(messages, str):
        messages = [messages]
    key = hash_args(settings.ollamna_model, messages)
    found = await ollama_cache.get_by_id(key)
    return found is not None


async def ollama_chat(prompt, system_prompt=None, history_messages=None, core_input: str = None, category: str = None, **kwargs) -> str:
    """
    Asynchronously interacts with the Ollama chat model, utilizing a caching mechanism to store and retrieve responses.

    Args:
        category:
        prompt (str): The user's input to be sent to the chat model.
        system_prompt (str, optional): An optional system-level prompt to guide the chat model. Defaults to None.
        history_messages (list, optional): A list of previous messages to provide context to the chat model. Defaults to an empty list.
        core_input (str, optional): An optional input string corresponding to the initial input. This is added to the cache to make it easier to detect the initial input rather than the directive prompt. Defaults to None.
        **kwargs: Additional keyword arguments to be passed to the chat model.

    Returns:
        str: The content of the response from the chat model.

    Caching:
        - Checks the cache for a stored response using a hash of the model and messages.
        - If a cached response is found, it is returned.
        - If no cached response is found, the chat model is queried, and the response is cached.
        - The cache is saved based on certain conditions (e.g., every 10th entry).

    Raises:
        Any exceptions raised by the Ollama client or cache operations.
    """
    if history_messages is None:
        history_messages = []
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    # cache lookup
    key = hash_args(settings.ollamna_model, messages)
    found = await ollama_cache.get_by_id(key)
    if found is not None:
        return found["content"]

    response = await ollama_client.chat(model=settings.ollamna_model, messages=messages, **kwargs)

    content = response["message"]["content"]

    # cache update
    await ollama_cache.upsert(
        {
            key: {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "input": core_input,
                "messages": len(messages),
                "content": content,
                "category": category,
                "model": settings.ollamna_model,
            }
        }
    )
    await ollama_cache.save()
    # save cache
    # save = kwargs.get("save", None)
    # if save is None:
    #     count = await ollama_cache.count()
    #     if count == 1 or count % 10 == 0:
    #         await ollama_cache.save()
    # else:
    #     if save:
    #         await ollama_cache.save()
    return content
