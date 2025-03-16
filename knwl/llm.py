import time
from typing import List

from knwl.llm_cache import LLMCache
from .models import KnwlLLMAnswer
from .settings import settings
from .utils import hash_args


class OllamaClient:
    def __init__(self):
        import ollama
        self.client = ollama.AsyncClient()

    async def ask(self, messages: List[dict]) -> KnwlLLMAnswer:
        start_time = time.time()
        response = await self.client.chat(model=settings.llm_model, messages=messages, options={"temperature": 0.0, "num_ctx": 32768})
        end_time = time.time()
        content = response["message"]["content"]
        return KnwlLLMAnswer(answer=content, messages=messages, timing=round(end_time - start_time, 2), llm_model=settings.llm_model, llm_service=settings.llm_service)


class OpenAIClient:
    def __init__(self):
        import openai
        self.client = openai.AsyncClient()

    async def ask(self, messages: List[dict]) -> KnwlLLMAnswer:
        start_time = time.time()
        found = await self.client.chat.completions.create(messages=messages, model=settings.llm_model)
        end_time = time.time()
        content = found.choices[0].message.content
        return KnwlLLMAnswer(answer=content, messages=messages, timing=round(end_time - start_time, 2), llm_model=settings.llm_model, llm_service=settings.llm_service)


class LLMClient:
    def __init__(self, cache: LLMCache = None):
        self.cache = cache
        if settings.llm_service == "ollama":
            self.client = OllamaClient()
        elif settings.llm_service == "openai":
            self.client = OpenAIClient()
        else:
            raise Exception(f"Unknown language service: {settings.llm_service}")

    async def is_cached(self, messages: str | List[str] | List[dict]) -> bool:
        if self.cache is None:
            return False
        return await self.cache.is_in_cache(messages, settings.llm_service, settings.llm_model)

    async def ask(self, prompt: str, system_prompt=None, history_messages=None, core_input: str = None, category: str = None, save: bool = True) -> KnwlLLMAnswer:
        messages = self.assemble_messages(prompt, system_prompt, history_messages)

        if self.cache is not None:
            found = await self.cache.get(messages, settings.llm_service,  settings.llm_model)
            if found is not None:
                return found
        # effectively asking the model
        answer: KnwlLLMAnswer = await self.client.ask(messages)
        answer.category = category
        answer.input = core_input
        # caching update, the 'save' flag is used to overrule the default behavior of saving the response
        if save:
            await self.cache.upsert(answer)
        return answer

    @staticmethod
    def assemble_messages(prompt: str, system_prompt=None, history_messages=None) -> List[dict]:
        if history_messages is None:
            history_messages = []
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})
        return messages

    @staticmethod
    def hash_args(*args):
        return hash_args(*args)


# note that LangChain has a ton of caching mechanisms in place: https://python.langchain.com/docs/integrations/llm_caching
llm_cache = LLMCache(caching=settings.llm_caching)
llm = LLMClient(llm_cache)
