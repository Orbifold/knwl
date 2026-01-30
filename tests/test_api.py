import json
from uuid import uuid4

from knwl.collect.wikipedia import WikipediaCollector
from knwl.format import print_knwl
from knwl.models import KnwlDocument
from tests.fixtures import *
from fastapi import status

# ============================================================================================
# Tests for Knowledge Graph API endpoints
# You don't have to run the API server to run these tests. A fixture creates the app instance.
# ============================================================================================
@pytest.mark.asyncio
async def test_facts(client):
    """
    Test the facts endpoint by creating, retrieving, and deleting a fact node.

    This test performs the following steps:
    1. Records the initial node count in the knowledge graph
    2. Creates a new fact node
    3. Polls the job endpoint to wait for fact creation to complete (up to 20 seconds)
    4. Verifies the job completed successfully and returns the correct node Id
    5. Retrieves the created fact node by Id and validates all fields match the input
    6. Verifies the node count increased by 1
    7. Deletes the fact node and verifies the count returns to the original value
    8. Tests error handling by attempting to retrieve a non-existent job Id
    9. Cleans up by deleting the created fact node

    """
    previous_count = client.get("/kg/node_count").json()["count"]
    id = str(uuid4())
    fact_data = {
        "name": f"Test Fact {id}",
        "content": "This is a test fact content.",
        "type": "test_type",
        "id": id,
    }
    response = client.post("/kg/fact", json=fact_data)
    assert response.status_code == status.HTTP_202_ACCEPTED
    job = response.json()  # Get the job response
    job_id = job["job_id"]
    # Poll for job completion
    import time

    for _ in range(20):
        job_status_response = client.get(f"/kg/job/{job_id}")
        assert job_status_response.status_code == status.HTTP_200_OK
        job_status = job_status_response.json()
        if job_status["state"] == "completed":
            break
        elif job_status["state"] == "failed":
            pytest.fail(
                f"Fact addition job failed with error: {job_status.get('error')}"
            )
        time.sleep(1)
    else:
        pytest.fail("Fact addition job did not complete in expected time.")

    node_id = job_status["result"]["id"]
    assert node_id == fact_data["id"]
    # Test retrieving the node by ID
    response = client.get(f"/kg/node/{fact_data['id']}")
    assert response.status_code == 200
    retrieved_fact = response.json()
    assert retrieved_fact["name"] == fact_data["name"]
    assert retrieved_fact["description"] == fact_data["content"]
    assert retrieved_fact["type"] == fact_data["type"]
    assert retrieved_fact["id"] == fact_data["id"]
    current_count = client.get("/kg/node_count").json()["count"]
    assert current_count == previous_count + 1
    client.delete(f"/kg/node/{fact_data['id']}")
    current_count = client.get("/kg/node_count").json()["count"]
    assert current_count == previous_count

    job_status_response = client.get(f"/kg/job/abcdefg12345")
    assert job_status_response.status_code == 404  # job not found


@pytest.mark.asyncio
async def test_ingest(client):
    ingest_data = {
        "content": "Boltzmann spent a great deal of effort in his final years defending his theories. He did not get along with some of his colleagues in Vienna, particularly Ernst Mach, who became a professor of philosophy and history of sciences in 1895. That same year Georg Helm and Wilhelm Ostwald presented their position on energetics at a meeting in Lübeck. They saw energy, and not matter, as the chief component of the universe. Boltzmann's position carried the day among other physicists who supported his atomic theories in the debate. In 1900, Boltzmann went to the University of Leipzig, on the invitation of Wilhelm Ostwald. Ostwald offered Boltzmann the professorial chair in physics, which became vacant when Gustav Heinrich Wiedemann died. After Mach retired due to bad health, Boltzmann returned to Vienna in 1902. In 1903, Boltzmann, together with Gustav von Escherich and Emil Müller, founded the Austrian Mathematical Society. His students included Karl Pribram, Paul Ehrenfest and Lise Meitner.",
        "name": "Ludwig Boltzmann Bio",
        "description": "A brief biography of Boltzmann.",
    }
    response = client.post("/kg/ingest", json=ingest_data)
    assert response.status_code == status.HTTP_202_ACCEPTED
    job = response.json()  # Get the job response
    job_id = job["job_id"]
    # Poll for job completion
    import time

    for i in range(20):
        job_status_response = client.get(f"/kg/job/{job_id}")
        assert job_status_response.status_code == status.HTTP_200_OK
        job_status = job_status_response.json()
        if job_status["state"] == "completed":
            break
        elif job_status["state"] == "failed":
            pytest.fail(f"Ingest job failed with error: {job_status.get('error')}")
        time.sleep(1)
    else:
        pytest.fail("Ingest job did not complete in expected time.")

    # Check the result
    assert "result" in job_status
    result = job_status["result"]
    assert "id" in result
    print(
        f"\n\nINGEST RESULT: {len(result['nodes'])} nodes and {len(result["edges"])} edges ingested."
    )
    print(json.dumps(result, indent=2))


@pytest.mark.asyncio
async def test_ask(client):
    payload = {"question": "Who did Boltzmann not get along with in Vienna?"}
    response = client.post("/kg/ask", json=payload)
    assert response.status_code == 200
    answer = response.json()
    # assert "answer" in answer
    assert "Ernst Mach" in answer["answer"]
    print(f"\n\nANSWER: {answer['answer']}")
    print(json.dumps(answer, indent=2))


@pytest.mark.asyncio
async def test_augment(client):
    payload = {"question": "Who did Boltzmann not get along with in Vienna?"}
    response = client.post("/kg/augment", json=payload)
    assert response.status_code == 200
    answer = response.json()
    assert len(answer["nodes"]) > 0
    assert len(answer["texts"]) > 0
    assert len(answer["edges"]) > 0
    # assert "Ernst Mach" in answer["answer"]
    print(f"\n\nAUGMENTATION")
    print(json.dumps(answer, indent=2))


@pytest.mark.asyncio
async def test_article_endpoint(client):
    """
    Test the /collect/wiki endpoint to fetch a Wikipedia article by title.
    1. Selects a random Wikipedia article title from the local library.
    2. Calls the /collect/wiki endpoint with the selected title.
    3. Verifies the response status and content.
    4. Validates that the returned article matches the requested title and contains content.
    """
    title = WikipediaCollector.take_random_wiki_title()
    print(f"Testing /wiki endpoint with article title: {title}")
    response = client.get(f"/collect/wiki?title={title}")
    assert response.status_code == 200, f"Failed to fetch article '{title}'"
    article = response.json()
    assert article["name"] == title
    assert "content" in article
    assert len(article["content"]) > 0


@pytest.mark.asyncio
async def test_url_endpoint(client):
    """
    Test the /collect/url endpoint to fetch content from a specified URL.
    1. Defines a test URL (example: Wikipedia page for "Ludwig Boltzmann").
    2. Calls the /collect/url endpoint with the test URL.
    3. Verifies the response status and content.
    4. Validates that the returned document contains expected content related to Ludwig Boltzmann.
    """
    url = "https://en.wikipedia.org/wiki/Ludwig_Boltzmann"
    print(f"Testing /url endpoint with URL: {url}")
    response = client.get(f"/collect/url?url={url}")
    assert response.status_code == 200, f"Failed to fetch content from URL '{url}'"
    document = response.json()
    assert "Ludwig Boltzmann" in document["name"]
    assert "content" in document
    assert len(document["content"]) > 0
    assert (
        "Boltzmann spent a great deal of effort in his final years defending his theories."
        in document["content"]
    )
    doc = KnwlDocument(**document)
    print_knwl(doc)

