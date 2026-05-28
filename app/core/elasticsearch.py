from elasticsearch import AsyncElasticsearch
import os

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

PAPER_INDEX = "papers"

es_client = AsyncElasticsearch([ES_URL])

# Index mapping — defines the structure of the papers in Elasticsearch
PAPERS_MAPPING = {
    "mappings": {
        "properties": {
            "paper_id": {"type": "keyword"},  # exact match only
            "owner_id": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "english"},
            "abstract": {"type": "text", "analyzer": "english"},
            "authors": {"type": "text", "analyzer": "english"},
            "categories": {"type": "keyword"},
            "arxiv_url": {"type": "keyword"},
            "published_at": {"type": "date"},
            "status": {"type": "keyword"},
        }
    }
}
