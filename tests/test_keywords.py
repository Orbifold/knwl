import pytest

from knwl.extraction.basic_keywords_extraction import BasicKeywordsExtraction
from knwl.format import print_knwl
pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_basic():
    input = """Gauss was a child prodigy in mathematics. When the elementary teachers noticed his intellectual abilities, they brought him to the attention of the Duke of Brunswick who sent him to the local Collegium Carolinum,[a] which he attended from 1792 to 1795 with Eberhard August Wilhelm von Zimmermann as one of his teachers. Thereafter the Duke granted him the resources for studies of mathematics, sciences, and classical languages at the University of Göttingen until 1798. His professor in mathematics was Abraham Gotthelf Kästner, whom Gauss called "the leading mathematician among poets, and the leading poet among mathematicians" because of his epigrams.[b] Astronomy was taught by Karl Felix Seyffer, with whom Gauss stayed in correspondence after graduation; Olbers and Gauss mocked him in their correspondence. On the other hand, he thought highly of Georg Christoph Lichtenberg, his teacher of physics, and of Christian Gottlob Heyne, whose lectures in classics Gauss attended with pleasure. Fellow students of this time were Johann Friedrich Benzenberg, Farkas Bolyai, and Heinrich Wilhelm Brandes.."""
    extractor = BasicKeywordsExtraction()
    keywords = await extractor.extract(input)
    assert keywords is not None
    # assert "Gauss" in keywords.low_level_keywords
    # assert "Education" in keywords.high_level_keywords
    print("Have not figured out how to unit test terminal visualization yet.")
    print_knwl(keywords)
