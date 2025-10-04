# Model comparison

The comparison shows that `gemma3:4b` and `qwen2.5:7b` perform best and fastest. Bigger is not better.


| **service** | **model**             | **mode** | **total** | **rag** | **llm** |
| ----------- | --------------------- | -------- | --------- | ------- | ------- |
| **ollama**  | llama3.3              | global   | 105.74    | 0.12    | 105.62  |
| **ollama**  | qwq                   | global   | 62.42     | 0.06    | 62.36   |
| **ollama**  | phi4                  | global   | 17.21     | 0.06    | 17.15   |
| **ollama**  | qwen2.5-coder:32b     | global   | 16.93     | 0.06    | 16.87   |
| **ollama**  | gemma3:27b            | global   | 12.74     | 0.07    | 12.67   |
| **ollama**  | o14                   | global   | 11.87     | 0.06    | 11.81   |
| **ollama**  | qwen2.5:14b           | global   | 11.69     | 0.06    | 11.63   |
| **ollama**  | gemma3:12b            | global   | 10.92     | 0.06    | 10.86   |
| **ollama**  | deepseek-coder-v2:16b | global   | 9.94      | 0.04    | 9.9     |
| **ollama**  | llama3.1              | global   | 6.7       | 0.06    | 6.64    |
| **ollama**  | llama3.2              | global   | 5.28      | 0.05    | 5.23    |
| **ollama**  | qwen2.5:7b            | global   | 4.66      | 0.05    | 4.61    |
| **ollama**  | o7                    | global   | 4.62      | 0.06    | 4.56    |
| **ollama**  | gemma3:4b             | global   | 4.26      | 0.07    | 4.19    |
| **ollama**  | qwen2.5-coder:3b      | global   | 0.0       | 0.0     | 0.0     |
| **ollama**  | qwen2.5-coder:16b     | global   | 0.0       | 0.0     | 0.0     |


