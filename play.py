import asyncio
from knwl import services, service, KnwlLLMAnswer
from knwl import OllamaClient
from knwl.format import print_knwl
from faker import Faker

fake = Faker()

async def main():

    # llm = OllamaClient()
    # print(f"{llm}")
    # a = await llm.ask("What is classical music?")
    # print_knwl(a)
    coll = []
    for i in range(30):
        coll.append(KnwlLLMAnswer(question=fake.sentence(nb_words=50), answer=fake.sentence(nb_words=200)))

    # print_knwl(coll)
    from knwl.format import render_knwl

    render_knwl(coll, format_type="markdown",           output_file="output.md", add_frontmatter=True)
asyncio.run(main())
