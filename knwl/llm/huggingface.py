import time
from typing import Optional

from knwl.di import defaults
from knwl.llm.llm_base import LLMBase
from knwl.llm.llm_cache_base import LLMCacheBase
from knwl.logging import log
from knwl.models.KnwlAnswer import KnwlAnswer


@defaults("@/llm/huggingface")
class HuggingFaceClient(LLMBase):
    """
    LLM client for HuggingFace models using the transformers library.
    
    Default model: Qwen/Qwen2.5-7B-Instruct
    """

    def __init__(
        self,
        model: str = None,
        temperature: float = None,
        context_window: int = None,
        caching_service: LLMCacheBase = None,
        device: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__()
        self._model_name = model
        self._temperature = temperature
        self._context_window = context_window
        self._device = device
        self._api_key = api_key  # HF_TOKEN for gated models

        self._caching_service: LLMCacheBase = caching_service
        self._pipeline = None
        self._tokenizer = None
        self.validate_params()

    def validate_params(self):
        if not self.caching_service:
            log.warn(
                "HuggingFaceClient: No caching service provided, caching disabled."
            )
        if (
            not isinstance(self.caching_service, LLMCacheBase)
            and self.caching_service is not None
        ):
            raise ValueError(
                f"HuggingFaceClient: caching_service must be an instance of LLMCacheBase, got {type(self.caching_service)}"
            )

    @property
    def pipeline(self):
        """Lazy initialization of HuggingFace pipeline"""
        if self._pipeline is None:
            try:
                import torch
                from transformers import pipeline, AutoTokenizer

                # Determine device
                if self._device:
                    device = self._device
                elif torch.cuda.is_available():
                    device = "cuda"
                elif torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"

                log.info(
                    f"HuggingFaceClient: Loading model {self._model_name} on {device}"
                )

                # Load tokenizer
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self._model_name,
                    token=self._api_key if self._api_key else None,
                )

                # Create text-generation pipeline
                self._pipeline = pipeline(
                    "text-generation",
                    model=self._model_name,
                    tokenizer=self._tokenizer,
                    device_map="auto" if device != "cpu" else None,
                    dtype=torch.float16 if device != "cpu" else torch.float32,
                    token=self._api_key if self._api_key else None,
                )

                log.info(f"HuggingFaceClient: Model {self._model_name} loaded successfully")

            except ImportError as e:
                log.error(
                    "HuggingFaceClient: transformers or torch not installed. "
                    "Install with: pip install transformers torch"
                )
                raise e
            except Exception as e:
                log.error(f"HuggingFaceClient: Failed to load model: {e}")
                raise e
        return self._pipeline

    @property
    def tokenizer(self):
        """Get tokenizer, initializing pipeline if needed"""
        if self._tokenizer is None:
            _ = self.pipeline  # Force initialization
        return self._tokenizer

    @property
    def model(self):
        return self._model_name

    @property
    def temperature(self):
        return self._temperature

    @property
    def context_window(self):
        return self._context_window

    @property
    def caching_service(self):
        return self._caching_service

    def _format_messages_for_model(self, messages: list[dict]) -> str:
        """
        Format messages using the model's chat template if available,
        otherwise use a simple format.
        """
        if self.tokenizer and hasattr(self.tokenizer, "apply_chat_template"):
            try:
                return self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            except Exception:
                pass

        # Fallback: simple formatting
        formatted = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                formatted += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted += f"<|user|>\n{content}\n"
            elif role == "assistant":
                formatted += f"<|assistant|>\n{content}\n"
        formatted += "<|assistant|>\n"
        return formatted

    async def ask(
        self,
        question: str,
        system_message: str = None,
        extra_messages: list[dict] = None,
        key: str = None,
        category: str = None,
        think: bool = False,
    ) -> KnwlAnswer:
        if not question:
            log.warn("HuggingFaceClient: ask called with empty question.")
            return None

        messages = self.assemble_messages(question, system_message, extra_messages)
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # Check cache first
        if self._caching_service is not None:
            cached = await self._caching_service.get(
                messages, "huggingface", self._model_name
            )
            if cached is not None:
                return cached

        start_time = time.time()

        # Format messages for the model
        prompt = self._format_messages_for_model(messages)

        # Generate response
        outputs = self.pipeline(
            prompt,
            max_new_tokens=self._context_window or 2048,
            temperature=self._temperature if self._temperature else 0.1,
            do_sample=self._temperature is not None and self._temperature > 0,
            pad_token_id=self.tokenizer.eos_token_id,
            return_full_text=False,
        )

        end_time = time.time()

        # Extract generated text
        content = outputs[0]["generated_text"].strip()

        answer = KnwlAnswer(
            question=question,
            answer=content,
            messages=messages,
            timing=round(end_time - start_time, 2),
            llm_model=self._model_name,
            llm_service="huggingface",
            key=key if key else question,
            category=category if category else "none",
        )

        if self._caching_service is not None:
            await self._caching_service.upsert(answer)

        return answer

    async def is_cached(self, messages: str | list[str] | list[dict]) -> bool:
        if self.caching_service is None:
            return False
        return await self._caching_service.is_in_cache(
            messages, "huggingface", self._model_name
        )

    def __repr__(self):
        return f"<HuggingFaceClient, model={self._model_name}, temperature={self._temperature}, caching_service={self._caching_service}>"

    def __str__(self):
        return self.__repr__()