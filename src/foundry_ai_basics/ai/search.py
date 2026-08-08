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
        "id": "order-1",
        "title": "Order: 55-inch 4K Smart TV",
        "content": (
            "Order ID: 12345. Customer purchased a 55-inch 4K Ultra HD Smart TV, "
            "brand: Contoso Electronics, model: UltraView 5500, serial number: TV-987654321. "
            "Order date: 2024-11-15. Delivery address: 123 Main St, Sydney, NSW. "
            "The TV features HDR, built-in Wi-Fi, and voice assistant support. "
        ),
        "category": "order",
    },
    {
        "id": "order-2",
        "title": "Order: Mountain Bike",
        "content": (
            "Order ID: 54321. Customer purchased a 21-speed mountain bike, "
            "brand: AdventureCycles, model: TrailBlazer 3000. "
            "Order date: 2023-07-10. Delivery address: 456 Elm St, Melbourne, VIC. "
            "The bike features front suspension and disc brakes."
        ),
        "category": "order",
    },
    {
        "id": "order-3",
        "title": "Order: Espresso Coffee Machine",
        "content": (
            "Order ID: 67890. Customer purchased an espresso coffee machine, "
            "brand: BrewMaster, model: ProBarista X2. "
            "Order date: 2024-01-22. Delivery address: 789 Oak Ave, Brisbane, QLD. "
            "The machine includes a milk frother and digital display."
        ),
        "category": "order",
    },
    {
        "id": "order-4",
        "title": "Order: Yoga Mat",
        "content": (
            "Order ID: 24680. Customer purchased a non-slip yoga mat, "
            "brand: ZenFit, model: ComfortMat 6mm. "
            "Order date: 2022-09-05. Delivery address: 321 Maple Rd, Perth, WA. "
            "The mat is eco-friendly and lightweight."
        ),
        "category": "order",
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

    # Get total count
    total_count = search_results.get_count()

    if total_count == 0:
        print("   No results found.\n")
        return []

    print(f"   Found {total_count} result(s):\n")

    results_formatted: list[dict[str, Any]] = []

    for i, result in enumerate(search_results, 1):
        print(f"{i}. {result['title']}")
        print(f"   Category: {result['category']}")
        print(f"   Score: {result.get('@search.score', 0):.4f}")
        print(f"   Reranker Score: {result.get('@search.reranker_score', 0):.4f}")

        # Show a snippet of the content
        content = result["content"]
        snippet = content[:120] + "..." if len(content) > 120 else content
        print(f"   Preview: {snippet}\n")

        results_formatted.append(
            {
                "rank": i,
                "title": result.get("title"),
                "category": result.get("category"),
                "score": result.get("@search.score"),
                "reranker_score": result.get("@search.reranker_score"),
                "content": result.get("content"),
            }
        )

    return results_formatted


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
