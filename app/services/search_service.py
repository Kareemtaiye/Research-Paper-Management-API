# from elasticsearch import AsyncElasticsearch
# import os

# ES_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

# PAPER_INDEX = "papers"

# es_client = AsyncElasticsearch([ES_URL])

# # Index mapping — defines the structure of the papers in Elasticsearch
# PAPERS_MAPPING = {
#     "mappings": {
#         "properties": {
#             "paper_id": {"type": "keyword"},  # exact match only
#             "owner_id": {"type": "keyword"},
#             "title": {"type": "text", "analyzer": "english"},
#             "abstract": {"type": "text", "analyzer": "english"},
#             "authors": {"type": "text", "analyzer": "english"},
#             "categories": {"type": "keyword"},
#             "arxiv_url": {"type": "keyword"},
#             "published_at": {"type": "date"},
#             "status": {"type": "keyword"},
#         }
#     }
# }


from app.core.elasticsearch import PAPER_INDEX, es_client, PAPERS_MAPPING


async def create_index_if_not_exists():
    """Create the papers index if it doesn't exist."""
    exists = await es_client.indices.exists(index=PAPER_INDEX)
    if not exists:
        await es_client.indices.create(index=PAPER_INDEX, body=PAPERS_MAPPING)


async def index_paper(paper: dict):
    """Add or update a paper in Elasticsearch."""
    await es_client.index(
        index=PAPER_INDEX,
        id=paper["id"],  # PostgreSQL UUID as ES document ID
        document={
            "paper_id": paper["id"],
            "owner_id": paper["owner_id"],
            "title": paper.get("title", ""),
            "abstract": paper.get("abstract", ""),
            "authors": " ".join(paper.get("authors") or []),
            "categories": paper.get("categories") or [],
            "arxiv_url": paper.get("arxiv_url", ""),
            "published_at": paper.get("published_at"),
            "status": paper.get("status", ""),
        },
    )


async def delete_paper(paper_id: str):
    """Remove a paper from Elasticsearch."""
    await es_client.delete(
        index=PAPER_INDEX, id=paper_id, ignore=[404]  # don't error if already gone
    )


async def search_papers(
    query: str,
    owner_id: str,
    limit: int = 10,
    offset: int = 0,
    category: str | None = None,
    from_date: str | None = None,
):
    """Search papers with relevance ranking."""

    # Base query — multi-field with boosting
    must_query = {
        "multi_match": {
            "query": query,
            "fields": ["title^5", "abstract^3", "authors^1"],
            "fuzziness": "AUTO",  # handles typos automatically
        }
    }

    # Filter — only return this user's papers
    filters = [{"term": {"owner_id": owner_id}}]

    # Optional category filter
    if category:
        filters.append({"term": {"categories": category}})

    # Optional date filter
    if from_date:
        filters.append({"range": {"published_at": {"gte": from_date}}})

    body = {
        "query": {"bool": {"must": [must_query], "filter": filters}},
        "from": offset,
        "size": limit,
        "highlight": {"fields": {"title": {}, "abstract": {"fragment_size": 150}}},
    }

    result = await es_client.search(index=PAPER_INDEX, body=body)

    hits = result["hits"]["hits"]
    total = result["hits"]["total"]["value"]

    return {
        "total": total,
        "results": [
            {
                "paper_id": hit["_source"]["paper_id"],
                "title": hit["_source"]["title"],
                "authors": hit["_source"]["authors"],
                "abstract": hit["_source"]["abstract"],
                "arxiv_url": hit["_source"]["arxiv_url"],
                "score": hit["_score"],
                "highlights": hit.get("highlight", {}),
            }
            for hit in hits
        ],
    }


async def get_all_es_papers():
    return await es_client.search(index=PAPER_INDEX, query={"match_all": {}})
