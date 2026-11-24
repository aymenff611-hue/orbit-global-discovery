"""ORBIT Search and Retrieval Module.

Provides search and retrieval capabilities over extracted content.
Integrates with Elasticsearch when available, otherwise provides
in-memory fallback for local development.
"""

import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger("orbit.api.search")


@dataclass
class SearchResult:
    """A single search result."""
    id: str
    source_id: str
    url: str
    title: Optional[str]
    content_snippet: str
    score: float
    language: Optional[str]
    timestamp: datetime


@dataclass
class SearchResponse:
    """Search response with results and metadata."""
    query: str
    total: int
    results: List[SearchResult] = field(default_factory=list)
    took_ms: float = 0.0


class SearchEngine:
    """Search and retrieval engine.

    Uses Elasticsearch when configured, otherwise falls back to
    in-memory search over stored content.
    """

    def __init__(self, settings=None, data_store=None):
        self.settings = settings
        self.data_store = data_store
        self._es_client = None
        self._es_available = False
        self._memory_index: List[Dict[str, Any]] = []

        if settings and settings.search_engine_url:
            self._try_init_elasticsearch()

    def _try_init_elasticsearch(self):
        """Try to initialize Elasticsearch client."""
        try:
            from elasticsearch import Elasticsearch
            self._es_client = Elasticsearch([self.settings.search_engine_url])
            # Test connection
            self._es_client.ping()
            self._es_available = True
            logger.info(f"Elasticsearch connected at {self.settings.search_engine_url}")
        except Exception as e:
            logger.warning(f"Elasticsearch not available: {e}. Using in-memory search.")
            self._es_available = False
            self._es_client = None

    def index_document(self, doc_id: str, source_id: str, url: str,
                       title: Optional[str], content: str,
                       language: Optional[str] = None,
                       timestamp: Optional[datetime] = None) -> bool:
        """Index a document for search."""
        doc = {
            "id": doc_id,
            "source_id": source_id,
            "url": url,
            "title": title or "",
            "content": content,
            "language": language,
            "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat(),
        }

        if self._es_available:
            try:
                index_name = f"{self.settings.search_index_prefix}_documents"
                self._es_client.index(index=index_name, id=doc_id, document=doc)
                return True
            except Exception as e:
                logger.warning(f"Elasticsearch index failed: {e}. Falling back to memory.")
                self._es_available = False

        # Fallback to memory
        self._memory_index.append(doc)
        return True

    def search(self, query: str, limit: int = 10,
               language: Optional[str] = None) -> SearchResponse:
        """Search indexed documents."""
        import time
        start = time.time()

        if self._es_available:
            return self._search_elasticsearch(query, limit, language, start)
        else:
            return self._search_memory(query, limit, language, start)

    def _search_elasticsearch(self, query: str, limit: int,
                              language: Optional[str],
                              start: float) -> SearchResponse:
        """Search using Elasticsearch."""
        try:
            index_name = f"{self.settings.search_index_prefix}_documents"
            must_clauses = [
                {"multi_match": {
                    "query": query,
                    "fields": ["title^2", "content"],
                    "type": "best_fields",
                }}
            ]

            if language:
                must_clauses.append({"term": {"language": language}})

            body = {
                "query": {"bool": {"must": must_clauses}},
                "size": limit,
            }

            resp = self._es_client.search(index=index_name, body=body)
            hits = resp["hits"]["hits"]
            total = resp["hits"]["total"]["value"] if isinstance(resp["hits"]["total"], dict) else resp["hits"]["total"]

            results = []
            for hit in hits:
                src = hit["_source"]
                results.append(SearchResult(
                    id=hit["_id"],
                    source_id=src.get("source_id", ""),
                    url=src.get("url", ""),
                    title=src.get("title"),
                    content_snippet=src.get("content", "")[:200],
                    score=hit["_score"],
                    language=src.get("language"),
                    timestamp=datetime.fromisoformat(src.get("timestamp", datetime.now().isoformat())),
                ))

            took_ms = (time.time() - start) * 1000
            return SearchResponse(
                query=query,
                total=total,
                results=results,
                took_ms=took_ms,
            )
        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            return self._search_memory(query, limit, language, start)

    def _search_memory(self, query: str, limit: int,
                       language: Optional[str],
                       start: float) -> SearchResponse:
        """Search using in-memory index (fallback)."""
        query_lower = query.lower()
        query_terms = query_lower.split()

        scored = []
        for doc in self._memory_index:
            if language and doc.get("language") != language:
                continue

            title = doc.get("title", "").lower()
            content = doc.get("content", "").lower()

            score = 0.0
            for term in query_terms:
                if term in title:
                    score += 2.0
                if term in content:
                    score += 1.0

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scored[:limit]:
            results.append(SearchResult(
                id=doc["id"],
                source_id=doc.get("source_id", ""),
                url=doc.get("url", ""),
                title=doc.get("title"),
                content_snippet=doc.get("content", "")[:200],
                score=score,
                language=doc.get("language"),
                timestamp=datetime.fromisoformat(doc.get("timestamp", datetime.now().isoformat())),
            ))

        took_ms = (time.time() - start) * 1000
        return SearchResponse(
            query=query,
            total=len(results),
            results=results,
            took_ms=took_ms,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            "elasticsearch_available": self._es_available,
            "memory_index_size": len(self._memory_index),
        }

    def __len__(self) -> int:
        return len(self._memory_index)


__all__ = ["SearchEngine", "SearchResult", "SearchResponse"]
