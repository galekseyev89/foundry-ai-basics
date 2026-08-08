from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
from openai import OpenAI

VECTOR_DIMENSIONS = 1536
VECTOR_PROFILE_NAME = "content-vector-profile"
VECTOR_ALGORITHM_NAME = "content-vector-hnsw"
SEMANTIC_CONFIG_NAME = "content-semantic-config"

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


def generate_embeddings(
    openai_client: OpenAI,
    embedding_deployment_name: str,
    text: str,
):
    """Generate a vector embedding for the given text."""
    response = openai_client.embeddings.create(
        input=text,
        model=embedding_deployment_name,
    )
    return response.data[0].embedding


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
        SearchField(
            name="content_vector",
            type="Collection(Edm.Single)",
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name=VECTOR_ALGORITHM_NAME)],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=VECTOR_ALGORITHM_NAME,
            )
        ],
    )
    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name=SEMANTIC_CONFIG_NAME,
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
        ]
    )
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )

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
    openai_client: OpenAI,
    embedding_deployment_name: str,
    documents: list[dict[str, str]] | None = None,
) -> bool:
    """Upload sample documents with embeddings to the search index."""
    documents_to_upload = documents or SAMPLE_DOCUMENTS
    print(f"Uploading {len(documents_to_upload)} document(s) to the search index...")

    try:
        documents_with_vectors = [
            _document_with_vector(
                openai_client,
                embedding_deployment_name,
                document,
            )
            for document in documents_to_upload
        ]
        results = search_client.upload_documents(documents=documents_with_vectors)
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
    openai_client: OpenAI,
    embedding_deployment_name: str,
    question: str,
    top: int = 5,
) -> list[dict[str, Any]]:
    """Search for documents that match the user's question."""
    print(f"\nSearching for: '{question}'")
    print("-" * 60)

    try:
        question_vector = generate_embeddings(
            openai_client,
            embedding_deployment_name,
            question,
        )
        search_results = search_client.search(
            search_text=question,
            vector_queries=[
                VectorizedQuery(
                    vector=question_vector,
                    fields="content_vector",
                    k_nearest_neighbors=top,
                )
            ],
            query_type="semantic",
            semantic_configuration_name=SEMANTIC_CONFIG_NAME,
            select=["id", "title", "content", "category"],
            include_total_count=True,
            top=top,
        )
    except Exception as error:
        print(f"Search failed: {error}")
        return []

    matches = [dict(result) for result in search_results]

    if not matches:
        print("No results found.")
        return []

    print(f"Found {len(matches)} result(s):\n")

    for index, result in enumerate(matches, 1):
        score = result.get("@search.score", 0)
        reranker_score = result.get("@search.reranker_score")
        content = result.get("content", "")
        snippet = content[:120] + "..." if len(content) > 120 else content

        print(f"{index}. {result.get('title', '(untitled)')}")
        print(f"   ID: {result.get('id', '(missing)')}")
        print(f"   Category: {result.get('category', '(uncategorized)')}")
        print(f"   Score: {score:.4f}")
        if reranker_score is not None:
            print(f"   Reranker score: {reranker_score:.4f}")
        print(f"   Preview: {snippet}\n")

    return matches


def _document_with_vector(
    openai_client: OpenAI,
    embedding_deployment_name: str,
    document: dict[str, str],
) -> dict[str, Any]:
    return {
        **document,
        "content_vector": generate_embeddings(
            openai_client,
            embedding_deployment_name,
            document["content"],
        ),
    }
