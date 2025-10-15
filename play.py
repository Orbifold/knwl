# ============================================================================================
# Use VSCode Interactive Python for best experience but you can also run this script directly.
# See https://code.visualstudio.com/docs/python/jupyter-support-py
# ============================================================================================
# %% 
# Demonstration of knwl formatting capabilities
 from knwl import services, service, KnwlLLMAnswer
from knwl import OllamaClient
from knwl.format import print_knwl
from faker import Faker
from knwl.format import render_knwl

# %%
fake = Faker()
# llm = OllamaClient()
# print(f"{llm}")
# a = await llm.ask("What is classical music?")
# print_knwl(a)
coll = []
for i in range(30):
    coll.append(
        KnwlLLMAnswer(
            question=fake.sentence(nb_words=50), answer=fake.sentence(nb_words=200)
        )
    )

print_knwl(coll)


# %%
