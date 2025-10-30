
## Context window and num_ctx

The context window (aka context length) is the maximum number of tokens a model can consider at once, it's determined by the model architecture. For example, if a model has a context window of 8192 tokens, it can process up to 8192 tokens of input and output combined.
The `num_ctx` on the other hand is the **Ollama-specific parameter** that sets the active context length for a given run. This means that if you set `num_ctx` to 8192, the model will utilize the full context window available for that model during inference. If you set it lower, say 4096, the model will only use up to 4096 tokens of context, even if the model supports more.

You can view the context window using Ollama's CLI command:

```bash
ollama show qwen2.5:14b
```

This renders:

```plaintext
 Model
    architecture        qwen2
    parameters          14.8B
    context length      32768
    embedding length    5120
    quantization        Q4_K_M

  Capabilities
    completion
    tools

  System
    You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

  License
    Apache License
    Version 2.0, January 2004

```

This tells you that Qwen2.5:14b has a context length of 32768 tokens.

## Custom Model
You can alter the context window of any Ollama model by creating a custom model with a different `num_ctx` parameter.

Create a `Modelfile` with the following content:

```
# My custom Modelfile to increase context length
FROM qwen3:8b

# Set the context window size (e.g., 4096, 8192, 16384, etc.)
PARAMETER num_ctx 8192
```
and save this as (for example) `Modelfile.custom`.

Then build the custom model using the Ollama CLI:

```bash
ollama create qwen3:8b-8k -f Modelfile.custom
```
This will fetch the based model if necessary and create a new model `qwen3:8b-8k` with an 8192 token context window.

You can also export a model alter the model file if you prefer:

```bash
ollama show --modelfile qwen2.5:14b > ./qwen2.5-14b-model
```
Edit this file to change the `num_ctx` parameter or set
```
PARAMETER num_ctx 8192
```
and build as before:

```bash
ollama create qwen2.5:14b-8k -f ./qwen2.5-14b-model
``` 

