from elasticsearch import AsyncElasticsearch
from app.core.config import settings

ES_URL = settings.prod_es_url if settings.is_production else settings.es_url

PAPER_INDEX = "papers"

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
