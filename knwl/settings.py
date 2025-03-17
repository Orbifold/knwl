import os


class Settings:
    """
    A global settings class to store diverse parameters for the codebase.
    """

    def __init__(self):
        self.working_dir = "./workdir"
        os.makedirs(self.working_dir, exist_ok=True)
        self.log_file = os.path.join(self.working_dir, "knwl.log")
        self.tokenize_model = "gpt-4o-mini"
        self.tokenize_size = 1024
        self.tokenize_overlap = 128

        # o7 is qwen2.5:7b with larger context window, o14 is similarly qwen2.5:14b
        self.llm_model = "gemma3:4b"
        # self.llm_model = "phi4"
        self.llm_service = "ollama"

        # self.llm_model = "gpt-4o-mini"
        # self.llm_service = "openai"

        self.entity_extract_max_gleaning = 1
        self.max_tokens = 32768
        self.summary_max = 20
        self.logging_enabled = False
        self.in_memory = True
        self.llm_caching = True

    def update(self, **kwargs):
        """
        Update settings with provided keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"Settings has no attribute '{key}'")

    def reset(self):
        """
        Reset settings to default values.
        """
        self.__init__()


# Create a global settings instance
settings = Settings()


def get_config(key):
    return getattr(settings, key, None)
