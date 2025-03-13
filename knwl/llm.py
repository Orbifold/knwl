from datetime import datetime
from typing import List

from .jsonStorage import JsonStorage
from .settings import settings
from .utils import hash_args


class LLMCache:
    """
    A thin wrapper around a JSON storage object to provide caching functionality for LLM.
    """

    def __init__(self, namespace: str = "llm", caching: bool = False):
        self.storage = JsonStorage(namespace, caching)

    async def is_in_cache(self, messages: str | List[str]) -> bool:
        if isinstance(messages, str):
            messages = [messages]
        key = hash_args(settings.llm_model, messages)
        found = await self.storage.get_by_id(key)
        return found is not None

    async def get_all_ids(self) -> list[str]:
        return await self.storage.get_all_ids()

    async def save(self):
        await self.storage.save()

    async def clear_cache(self):
        await self.storage.clear_cache()

    async def get_by_id(self, id):
        return await self.storage.get_by_id(id)

    async def get_by_ids(self, ids, fields=None):
        return await self.storage.get_by_ids(ids, fields=fields)

    async def filter_new_ids(self, data: list[str]) -> set[str]:
        return await self.storage.filter_new_ids(data)

    async def upsert(self, data: dict[str, object]):
        return await self.storage.upsert(data)


class OllamaClient:
    def __init__(self):
        import ollama
        self.client = ollama.AsyncClient()

    async def ask(self, messages: List[dict]) -> str:
        response = await self.client.chat(model=settings.llm_model, messages=messages, options={"temperature": 0.0, "num_ctx": 32768})
        content = response["message"]["content"]
        return content


class OpenAIClient:
    def __init__(self):
        import openai
        self.client = openai.AsyncClient()

    async def ask(self, messages: List[dict]) -> str:
        found = await self.client.chat.completions.create(messages=messages, model=settings.llm_model)
        return found.choices[0].message.content


class LLMClient:
    def __init__(self, cache: LLMCache = None):
        self.cache = cache
        if settings.llm_service == "ollama":
            self.client = OllamaClient()
        elif settings.llm_service == "openai":
            self.client = OpenAIClient()
        else:
            raise Exception(f"Unknown language service: {settings.llm_service}")

    async def is_cached(self, messages: str | List[str]) -> bool:
        if self.cache is None:
            return False
        return await self.cache.is_in_cache(messages)

    async def ask(self, prompt: str, system_prompt=None, history_messages=None, core_input: str = None, category: str = None, save:bool=True) -> str:
        if history_messages is None:
            history_messages = []
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})
        model = settings.llm_model

        if self.cache is not None:
            key = hash_args(model, messages)
            found = await self.cache.get_by_id(key)
            if found is not None:
                return found["content"]
        # effectively asking the model
        answer = await self.client.ask(messages)

        # caching update, the 'save' flag is used to overrule the default behavior of saving the response
        if save:
            await self.cache.upsert(
                {
                    "key": {
                        "timestamp": datetime.now().isoformat(),
                        "prompt": prompt,
                        "input": core_input,
                        "messages": len(messages),
                        "content": answer,
                        "category": category,
                        "model": settings.llm_model,
                    }
                }
            )
        return answer

    @staticmethod
    def hash_args(*args):
        return hash_args(*args)


# note that LangChain has a ton of caching mechanisms in place: https://python.langchain.com/docs/integrations/llm_caching
llm_cache = LLMCache(caching=settings.llm_caching)
llm = LLMClient(llm_cache)
