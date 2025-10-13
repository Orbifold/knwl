Chunking is a simple process of breaking down large texts into smaller, more manageable pieces called chunks. The underlying problem is to figure out what a character, a word, or a sentence is. It's more subtle than just splitting arrays.
LLMs come to the rescue here and tokenizers like tiktoken are crucial for neural networks internally and for consumers to understand the size of their inputs.

So, while the chunking inside Knwl is straightforward, underneath it is a deterministic tokenization library (Byte Pair Encoding or BPE) that is used by OpenAI models.

To see chunking in action you need to override the defaults a bit since the default chunk size is 1024 tokens with an overlap of 128 tokens. This is too large for demonstration purposes so we will set it to 20 tokens with no overlap:

```python
import asyncio
from knwl import services, ChunkingBase


async def main():
    config = {
        "chunking": {
            "tiktoken": {
                "chunk_size": 20,
                "chunk_overlap": 0,
            },
        }
    }
    s: ChunkingBase = services.get_service("chunking", override=config)
    text = """In 1939, upon arriving late to his statistics course at the University of California, Berkeley, George Dantzig — a first-year graduate student — copied two problems off the blackboard, thinking they were a homework assignment. He found the homework “harder to do than usual,” he would later recount, and apologized to the professor for taking some extra days to complete it. A few weeks later, his professor told him that he had solved two famous open problems in statistics. Dantzig’s work would provide the basis for his doctoral dissertation and, decades later, inspiration for the film Good Will Hunting.

Dantzig received his doctorate in 1946, just after World War II, and he soon became a mathematical adviser to the newly formed U.S. Air Force. As with all modern wars, World War II’s outcome depended on the prudent allocation of limited resources. But unlike previous wars, this conflict was truly global in scale, and it was won in large part through sheer industrial might. The U.S. could simply produce more tanks, aircraft carriers and bombers than its enemies. Knowing this, the military was intensely interested in optimization problems — that is, how to strategically allocate limited resources in situations that could involve hundreds or thousands of variables.

The Air Force tasked Dantzig with figuring out new ways to solve optimization problems such as these. In response, he invented the simplex method, an algorithm that drew on some of the mathematical techniques he had developed while solving his blackboard problems almost a decade before.

Nearly 80 years later, the simplex method is still among the most widely used tools when a logistical or supply-chain decision needs to be made under complex constraints. It’s efficient and it works. “It has always run fast, and nobody’s seen it not be fast,” said Sophie Huiberts of the French National Center for Scientific Research (CNRS).

At the same time, there’s a curious property that has long cast a shadow over Dantzig’s method. In 1972, mathematicians proved that the time it takes to complete a task could rise exponentially with the number of constraints. So, no matter how fast the method may be in practice, theoretical analyses have consistently offered worst-case scenarios that imply it could take exponentially longer. For the simplex method, “our traditional tools for studying algorithms don’t work,” Huiberts said."""
    result = await s.chunk(text, source_key="test")
    for chunk in result:
        print("----chunk----")
        print(chunk)


asyncio.run(main())
```

This will print out the chunks of text, each containing up to 20 tokens. You can adjust the `chunk_size` and `chunk_overlap` parameters to see how they affect the chunking process.
