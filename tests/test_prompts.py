import pytest
from knwl.prompts.prompts import prompts
pytestmark = pytest.mark.basic
    

def test_summarization():
    prompt = prompts.summarization.summarize("ABC")
    assert prompt.index("""
-Data-
Description List: 
ABC""") > -1
    prompt = prompts.summarization.summarize_entity(["Name", "Date"], "Test")
    assert prompt.index("Entities: Name, Date") > -1


def test_extraction():
    prompt = prompts.extraction.full_graph_extraction("This is a test")
    assert prompt.index("Text: This is a test") > -1
    print("")
    print(prompt)

