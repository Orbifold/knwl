import pytest

from knwl.summarization.ollama import OllamaSummarization

pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_summarization():
    summ = OllamaSummarization()
    result = await summ.summarize("This is a test.")
    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "This is a test."
    summ = OllamaSummarization(max_tokens=100)
    descriptions = [
        "Elephants are the world's largest land mammals, known for their massive bodies, long trunks, large ears, and tusks. They are highly intelligent, social animals found in Africa and Asia, and are herbivorous, spending much of their time eating vegetation. Their unique trunks serve as an extension of the nose and upper lip, used for a variety of tasks, and their large ears help to regulate body temperature.",
        "The trunk, or proboscis, of the elephant is one of the most versatile organs to have evolved among mammals. This structure is unique to members of the order Proboscidea, which includes the extinct mastodons and mammoths. Anatomically, the trunk is a combination of the upper lip and nose; the nostrils are located at the tip. The trunk is large and powerful, weighing about 130 kg (290 pounds) in an adult male and capable of lifting a load of about 250 kg. However, it is also extremely dexterous, mobile, and sensitive, which makes it appear almost independent of the rest of the animal. The proboscis comprises 16 muscles.",
    ]
    result = await summ.summarize(descriptions)
    assert isinstance(result, str)
    assert len(result) > 0
    summary_count = await summ.chunker.count_tokens(result)
    initial_count = await summ.chunker.count_tokens(" ".join(descriptions))
    # assert summary_count <  summ.max_tokens
    assert summary_count < initial_count
    print("\n------------------Generic------------------")
    print(result)

    result = await summ.summarize(descriptions, entity_or_relation_name="Mammals")
    print("\n------------------Mammals------------------")
    print(result)
