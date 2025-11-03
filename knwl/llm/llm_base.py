from abc import ABC, abstractmethod
from typing import List

from knwl.framework_base import FrameworkBase
from knwl.llm.llm_cache_base import LLMCacheBase
from knwl.models.KnwlAnswer import KnwlAnswer
from knwl.services import services


class LLMBase(FrameworkBase, ABC):

    @abstractmethod
    async def ask(        
        self,
        question: str,
        system_message: str = None,
        extra_messages: list[dict] = None,
        key: str = None,
        category: str = None
    ) -> KnwlAnswer:
        """
        Asynchronously sends a question to the LLM and returns the response.

        Args:
            question (str): The question or prompt to send to the LLM.
            system_message (str, optional): A system message that provides context or instructions for the LLM. 
                Defaults to None.
            extra_messages (list[dict], optional): Additional messages to include in the conversation history. 
                Each message should be a dictionary with appropriate format for the LLM provider. 
                Defaults to None.
            key (str, optional): An API key or authentication token to use for this specific request. 
                If None, uses the default key configured for the LLM. Defaults to None.
            category (str, optional): A category label for the question, used for tracking or filtering purposes. 
                Defaults to None.

        Returns:
            KnwlLLMAnswer: An object containing the LLM's response and associated metadata.

        """
        ...

    @abstractmethod
    async def is_cached(self, messages: str | list[str] | list[dict]) -> bool:
        ...

    def get_caching_service(
        self, caching_service_name, override=None
    ) -> LLMCacheBase | None:

        if caching_service_name is None or caching_service_name is False:
            return None
        if isinstance(caching_service_name, LLMCacheBase):
            return caching_service_name
        if isinstance(caching_service_name, str):
            return services.instantiate_service(
                "llm_caching", caching_service_name, override=override
            )
        # Default to no caching
        return None

    @staticmethod
    def assemble_messages(
        user_message: str, system_message=None, extra_messages=None
    ) -> list[dict]:
        if user_message is None or user_message.strip() == "":
            raise ValueError("user_message cannot be None or empty.")
        if extra_messages is None:
            extra_messages = []
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.extend(extra_messages)
        messages.append({"role": "user", "content": user_message})
        return messages
