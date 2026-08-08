from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchIndex,
    SimpleField,
)

SAMPLE_DOCUMENTS = [
    {
        "id": "1",
        "title": "Azure Machine Learning Tutorial",
        "content": (
            "Azure Machine Learning provides a cloud-based environment for "
            "training and deploying ML models."
        ),
        "category": "tutorial",
    },
    {
        "id": "2",
        "title": "Introduction to Python Programming",
        "content": (
            "Python is a versatile programming language used for web development, "
            "data science, and AI."
        ),
        "category": "programming",
    },
    {
        "id": "3",
        "title": "Azure AI Search Best Practices",
        "content": (
            "Learn how to optimize Azure AI Search for performance and cost "
            "efficiency."
        ),
        "category": "best-practices",
    },
    {
        "id": "4",
        "title": "Cloud Computing Fundamentals",
        "content": "Understanding cloud computing concepts including IaaS, PaaS, and SaaS.",
        "category": "fundamentals",
    },
    {
        "id": "5",
        "title": "Getting Started with Docker",
        "content": (
            "Docker containers help package applications with their dependencies "
            "for consistent deployment."
        ),
        "category": "devops",
    },
]


def create_index(
    index_client: SearchIndexClient,
    index_name: str,
) -> bool:
    """Create the sample Azure AI Search index if it does not already exist."""
    print(f"Creating search index '{index_name}'...")

    fields = [
        SimpleField(name="id", type="Edm.String", key=True),
        SearchableField(name="title", type="Edm.String"),
        SearchableField(name="content", type="Edm.String"),
        SimpleField(name="category", type="Edm.String", filterable=True),
    ]
    index = SearchIndex(name=index_name, fields=fields)

    try:
        index_client.get_index(index_name)
    except ResourceNotFoundError:
        try:
            index_client.create_index(index)
        except Exception as error:
            print(f"Failed to create search index: {error}")
            return False

        print(f"Created search index '{index_name}'.")
        return True
    except Exception as error:
        print(f"Failed to check search index: {error}")
        return False

    print(f"Search index '{index_name}' already exists.")
    return False


def upload_documents(
    search_client: SearchClient,
    documents: list[dict[str, str]] | None = None,
) -> bool:
    """Upload sample documents to the search index."""
    documents_to_upload = documents or SAMPLE_DOCUMENTS
    print(f"Uploading {len(documents_to_upload)} document(s) to the search index...")

    try:
        results = search_client.upload_documents(documents=documents_to_upload)
    except Exception as error:
        print(f"Failed to upload documents: {error}")
        return False

    failed_results = [result for result in results if not result.succeeded]

    if failed_results:
        print("Some documents failed to upload:")
        for result in failed_results:
            error = getattr(result, "error_message", "No error message returned.")
            print(f"- {result.key}: {error}")
        return False

    print("Documents uploaded successfully.")
    return True


def search_documents(
    search_client: SearchClient,
    question: str,
    top: int = 5,
) -> list[dict[str, Any]]:
    """Search for documents that match the user's question."""
    print(f"\nSearching for: '{question}'")
    print("-" * 60)

    try:
        search_results = search_client.search(
            search_text=question,
            select=["id", "title", "content", "category"],
            include_total_count=True,
            top=top,
        )
        matches = [dict(result) for result in search_results]
    except Exception as error:
        print(f"Search failed: {error}")
        return []

    if not matches:
        print("No results found.")
        return []

    print(f"Found {len(matches)} result(s):\n")

    for index, result in enumerate(matches, 1):
        score = result.get("@search.score", 0)
        content = result.get("content", "")
        snippet = content[:120] + "..." if len(content) > 120 else content

        print(f"{index}. {result.get('title', '(untitled)')}")
        print(f"   ID: {result.get('id', '(missing)')}")
        print(f"   Category: {result.get('category', '(uncategorized)')}")
        print(f"   Score: {score:.4f}")
        print(f"   Preview: {snippet}\n")

    return matches
