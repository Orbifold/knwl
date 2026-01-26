# import typer

# def main():
#     options = ["apple", "banana", "cherry"]

#     for i, opt in enumerate(options, start=1):
#         typer.echo(f"{i}. {opt}")

#     choice = typer.prompt("Pick a fruit", type=int)
#     selected = options[choice - 1]

#     typer.echo(f"You chose: {selected}")

# if __name__ == "__main__":
#     typer.run(main)
# ============================================================================================

# from transformers import AutoModelForCausalLM, AutoTokenizer

# model_name = "Ihor/Text2Graph-R1-Qwen2.5-0.5b"

# model = AutoModelForCausalLM.from_pretrained(
#     model_name, dtype="auto", device_map="auto"
# )
# tokenizer = AutoTokenizer.from_pretrained(model_name)

# text = """Augusta Ada King, Countess of Lovelace (née Byron; 10 December 1815 – 27 November 1852), also known as Ada Lovelace, was an English mathematician and writer chiefly known for work on Charles Babbage's proposed mechanical general-purpose computer, the analytical engine. She was the first to recognise the machine had applications beyond pure calculation. Lovelace is often considered the first computer programmer.
# Lovelace was the only legitimate child of poet Lord Byron and reformer Anne Isabella Milbanke. Lord Byron separated from his wife a month after Ada was born, and died when she was eight. Although often ill in childhood, Lovelace pursued her studies assiduously. She married William King in 1835. King was a Baron, and was created Viscount Ockham and 1st Earl of Lovelace in 1838. The name Lovelace was chosen because Ada was descended from the extinct Baron Lovelaces. The title given to her husband thus made Ada the Countess of Lovelace.
# Lovelace's educational and social exploits brought her into contact with scientists such as Andrew Crosse, Charles Babbage, David Brewster, Charles Wheatstone and Michael Faraday, and the author Charles Dickens, contacts which she used to further her education. Lovelace described her approach as "poetical science" and herself as an "Analyst (& Metaphysician)". When she was eighteen, Lovelace's mathematical talents led her to a long working relationship and friendship with fellow British mathematician Charles Babbage. She was particularly interested in Babbage's work on the analytical engine. Lovelace first met him on 5 June 1833, when she and her mother attended one of Charles Babbage's Saturday night soirées with their mutual friend, and Lovelace's private tutor, Mary Somerville.
# Though Babbage's Analytical Engine was never constructed and did not influence the invention of electronic computers, it has been recognised as a Turing-complete general-purpose computer, which anticipated the essential features of a modern electronic computer. Babbage is therefore known as the "father of computers," and Lovelace is credited with several computing "firsts" for her collaboration with him. Lovelace translated an article by the military engineer Luigi Menabrea about the Analytical Engine, supplementing it with seven long explanatory notes. These described a method of using the machine to calculate Bernoulli numbers which is often called the first published computer program. She developed a vision of the capability of computers to go beyond mere calculating or number-crunching, while many others, including Babbage, focused only on those capabilities. Lovelace was the first to point out the possibility of encoding information besides mere arithmetical figures, such as music, and manipulating it with such a machine. Her mindset of "poetical science" led her to ask questions about the analytical engine, examining how individuals and society relate to technology as a collaborative tool. Ada is widely commemorated, including in the names of a programming language, roads, buildings and institutes, as well as programmes, lectures and courses. There are plaques, statues, paintings, literary and non-fiction works."""
# prompt = "Analyze this text, identify the entities, and extract meaningful relationships as per given instructions:{}"
# messages = [
#     {
#         "role": "system",
#         "content": (
#             "You are an assistant trained to process any text and extract named entities and relations from it. "
#             "Your task is to analyze user-provided text, identify all unique and contextually relevant entities, and infer meaningful relationships between them"
#             "Output the annotated data in JSON format, structured as follows:\n\n"
#             """{"entities": [{"type": entity_type_0", "text": "entity_0", "id": 0}, "type": entity_type_1", "text": "entity_1", "id": 0}], "relations": [{"head": "entity_0", "tail": "entity_1", "type": "re_type_0"}]}"""
#         ),
#     },
#     {"role": "user", "content": prompt.format(text)},
# ]
# text = tokenizer.apply_chat_template(
#     messages, tokenize=False, add_generation_prompt=True
# )
# model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# generated_ids = model.generate(**model_inputs, max_new_tokens=512)
# generated_ids = [
#     output_ids[len(input_ids) :]
#     for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
# ]

# response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

# print(response)
# ============================================================================================
from knwl.di import service
from knwl.format import print_knwl

@service("llm", variant="huggingface")
async def my_func(llm=None):
    answer = await llm.ask("What is algebraic topology?")
    print_knwl(answer)
import asyncio
asyncio.run(my_func())