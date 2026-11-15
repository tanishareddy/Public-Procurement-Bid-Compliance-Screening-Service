import os
import re
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

CHROMA_DIR = "./data/chroma_db"
COLLECTION_NAME = "bid_compliance_corpus"

class CorpusRetriever:
    _instance = None

    def __init__(self, persist_dir: str = CHROMA_DIR):
        self.chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_collection(COLLECTION_NAME)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def search(self, query: str, top_k: int = 4, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves relevant passages using fast token-overlap & keyword-weighted ranking,
        guaranteeing zero external network calls, zero model download hangs, and ultra-low latency.
        """
        all_docs = self.collection.get()
        if not all_docs or not all_docs.get("documents"):
            return []

        query_terms = set(re.findall(r'\w+', query.lower()))
        scored = []

        for doc_id, doc_text, meta in zip(all_docs["ids"], all_docs["documents"], all_docs["metadatas"]):
            if doc_type and meta.get("document_type") != doc_type:
                continue

            doc_text_lower = doc_text.lower()
            doc_terms = set(re.findall(r'\w+', doc_text_lower))
            
            # Intersection score
            overlap = len(query_terms.intersection(doc_terms))
            
            # Bonus weighting for clause matches or exact phrase presence
            bonus = 0.0
            if query.lower() in doc_text_lower:
                bonus += 5.0
            for term in query_terms:
                if term in meta.get("clause_number", "").lower():
                    bonus += 3.0
                if term in ["startup", "mse", "turnover", "experience", "emd", "relaxation", "173", "170"]:
                    if term in doc_text_lower:
                        bonus += 1.5

            total_score = overlap + bonus
            if total_score > 0:
                scored.append((total_score, {
                    "id": doc_id,
                    "text": doc_text,
                    "document_name": meta.get("document_name", ""),
                    "document_type": meta.get("document_type", ""),
                    "issuing_authority": meta.get("issuing_authority", ""),
                    "clause_number": meta.get("clause_number", ""),
                    "score": round(total_score, 2)
                }))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def lookup_clause(self, clause_keyword: str) -> List[Dict[str, Any]]:
        """
        Deterministic lookup for a specific clause or rule identifier.
        """
        all_docs = self.collection.get()
        matched = []
        kw = clause_keyword.lower().strip()
        for doc_id, doc_text, meta in zip(all_docs["ids"], all_docs["documents"], all_docs["metadatas"]):
            if kw in meta.get("clause_number", "").lower() or kw in doc_text.lower():
                matched.append({
                    "id": doc_id,
                    "text": doc_text,
                    "document_name": meta.get("document_name", ""),
                    "document_type": meta.get("document_type", ""),
                    "issuing_authority": meta.get("issuing_authority", ""),
                    "clause_number": meta.get("clause_number", "")
                })
        return matched[:3]
