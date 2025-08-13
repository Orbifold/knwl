import asyncio

import sys

sys.path.append('..')
from knwl import Knwl, QueryParam, QueryModes, settings

knwl = Knwl()


async def set_facts():
    await knwl.input('John is married to Anna.', "Married")
    await knwl.input('Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.', "Family")
    await knwl.input('John has been working for the past ten years on AI and robotics. He knows a lot about the subject.', "Work")


async def query(mode: QueryModes):
    r = await knwl.query("Who is John?", QueryParam(mode=mode))
    with open(f"{settings.llm_model}-{mode}.txt", 'w') as f:
        f.write(r.answer)
    with open('speed.txt', 'a') as f:
        f.write(f"{settings.llm_service}, {settings.llm_model}, {mode}, {r.total_time}, {r.rag_time}, {r.llm_time}\n")


async def run():
    await set_facts()
    models = [
        "qwen2.5-coder:3b",
        "qwen2.5-coder:32b",
        "o7",
        "o14",
        "phi4",
        "deepseek-coder-v2:16b",
        "gemma3:4b",
        "gemma3:12b",
        "gemma3:27b",
        "llama3.3",
        "llama3.2",
        "llama3.1",
        "qwen2.5:7b",
        "qwen2.5:14b",
        "qwq"
    ]
    for model in models:
        settings.llm_model = model
        try:
            await query("naive")
            await query("hybrid")
            await query("local")
            await query("global")
        except Exception as e:
            print(e)


asyncio.run(run())
