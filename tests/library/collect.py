# ============================================================================================
# Collects diverse articles from Wikipedia for testing and demo purposes.
# Install the package via `uv add wikipedia-api`
# See here: https://github.com/martin-majlis/Wikipedia-API
# ============================================================================================
import os
import wikipediaapi
import random

library = {
    "mathematics": [
        "Isaac Newton",
        "Leonhard Euler",
        "Carl Friedrich Gauss",
        "Emmy Noether",
        "Srinivasa Ramanujan",
        "Euclid",
        "Archimedes",
        "Ada Lovelace",
        "Alan Turing",
        "John von Neumann",
        "Évariste Galois",
        "Sophie Germain",
        "David Hilbert",
        "Kurt Gödel",
        "Maryam Mirzakhani",
        "Paul Erdős",
        "Bernhard Riemann",
        "Pierre de Fermat",
        "Blaise Pascal",
        "René Descartes",
        "Pythagoras",
        "Hypatia",
        "Roger Penrose",
        "Omar Khayyam",
        "Fibonacci",
    ],
    "biology": [
        "Charles Darwin",
        "Gregor Mendel",
        "Louis Pasteur",
        "Jane Goodall",
        "Rachel Carson",
        "Rosalind Franklin",
        "Barbara McClintock",
        "Carl Linnaeus",
        "James Watson",
        "Francis Crick",
        "Richard Dawkins",
        "E. O. Wilson",
        "Lynn Margulis",
        "Alexander Fleming",
        "Jonas Salk",
        "Francis Collins",
    ],
    "business": [
        "Steve Jobs",
        "Bill Gates",
        "Warren Buffett",
        "Jeff Bezos",
        "Elon Musk",
        "Henry Ford",
        "Andrew Carnegie",
        "John D. Rockefeller",
        "Peter Drucker",
        "Jack Welch",
        "Mary Barra",
        "Indra Nooyi",
        "Satya Nadella",
        "Tim Cook",
        "Mark Zuckerberg",
    ],
    "finance": [
        "Adam Smith",
        "John Maynard Keynes",
        "Milton Friedman",
        "Benjamin Graham",
        "Ray Dalio",
        "George Soros",
        "Janet Yellen",
        "Paul Volcker",
        "Alan Greenspan",
        "Christine Lagarde",
        "Burton Malkiel",
        "Eugene Fama",
        "Robert Shiller",
        "Hyman Minsky",
        "Friedrich Hayek",
    ],
    "arts": [
        "Leonardo da Vinci",
        "Pablo Picasso",
        "Vincent van Gogh",
        "Frida Kahlo",
        "Michelangelo",
        "Claude Monet",
        "Georgia O'Keeffe",
        "Andy Warhol",
        "Salvador Dalí",
        "Rembrandt",
        "Yayoi Kusama",
        "Banksy",
        "Jean-Michel Basquiat",
        "Gustav Klimt",
        "Henri Matisse",
    ],
    "literature": [
        "William Shakespeare",
        "Jane Austen",
        "Leo Tolstoy",
        "Fyodor Dostoevsky",
        "Virginia Woolf",
        "Gabriel García Márquez",
        "Toni Morrison",
        "Ernest Hemingway",
        "Maya Angelou",
        "Charles Dickens",
        "Emily Dickinson",
        "James Joyce",
        "Chinua Achebe",
        "Haruki Murakami",
        "Margaret Atwood",
    ],
}


async def fetch_page_text(page_title: str) -> str:
    """
    Fetches the text of a Wikipedia page given its title.
    """
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent="Knwl (https://knwl.ai)",
        language="en",
        extract_format=wikipediaapi.ExtractFormat.WIKI,
    )
    page = wiki_wiki.page(page_title)
    return page.text


async def collect_library():
    """
    Collects articles from Wikipedia and saves them as markdown files in the respective
    category folders.

    The `get_library_article` function fetches the articles as needed, this function fetches all in one go.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for cat in library:
        os.makedirs(os.path.join(current_dir, cat), exist_ok=True)
        for m in library[cat]:
            file_path = os.path.join(current_dir, cat, f"{m.replace(' ', '_')}.md")
            if os.path.exists(file_path):
                continue

            try:
                p = await fetch_page_text(m)
                with open(
                    file_path,
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(p.text)
                print(f"\033[92m✓\033[0m {m}")
            except Exception as e:
                print(f"\033[91m✗ \033[0m {m}")
                print(e)


async def get_random_library_article(category: str = None) -> str:
    """
    Fetches a random article from the specified category in the local library cache or from Wikipedia if not cached.
    If no category is specified, a random category is chosen.
    """
    if category is None:
        category = random.choice(list(library.keys()))
    if category not in library:
        raise ValueError(f"Category '{category}' not found in library.")

    article = random.choice(library[category])
    return await get_library_article(category, article)

async def get_library_article(category: str, title: str) -> str:
    """
    Fetches a specific article from the local library cache or from Wikipedia if not cached.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join(current_dir, category, f"{title.replace(' ', '_')}.md")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            article = f.read()
    else:
        os.makedirs(os.path.join(current_dir, category), exist_ok=True)
        article = await fetch_page_text(title)
        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(article)
    return article


if __name__ == "__main__":
    import asyncio
    asyncio.run(collect_library()) # fetch and cache all articles
