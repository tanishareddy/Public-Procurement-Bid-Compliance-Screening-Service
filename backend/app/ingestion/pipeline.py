import os
import hashlib
import json
import re
from datetime import datetime
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

RAW_DIR = "data/corpus/raw"
PROCESSED_DIR = "data/corpus/processed"
CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "bid_compliance_corpus"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class CorpusIngestionPipeline:
    def __init__(self, persist_dir: str = CHROMA_DIR, model_name: str = EMBEDDING_MODEL):
        self.persist_dir = persist_dir
        self.model_name = model_name
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        os.makedirs(persist_dir, exist_ok=True)
        
        print(f"Loading embedding model: {model_name}...")
        self.encoder = SentenceTransformer(model_name)
        
        self.chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Procurement tenders and statutory compliance rules"}
        )

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def chunk_document(self, text: str, doc_name: str, doc_type: str, authority: str) -> List[Dict[str, Any]]:
        """
        Chunks documents cleanly around clauses, sections, and rules.
        """
        chunks = []
        # Split on Rule, Clause, Section, or paragraph headers
        sections = re.split(r'\n(?=(?:Rule\s+\d+|Clause\s+[\d\.]+|Section\s+\d+|\d+\.\s+))', text)
        
        chunk_idx = 0
        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean or len(sec_clean) < 30:
                continue
            
            # Extract clause/rule identifier if present
            clause_match = re.search(r'(Rule\s+\d+(\([a-z0-9]+\))?|Clause\s+[\d\.]+|Section\s+\d+(\([a-z0-9]+\))?)', sec_clean, re.IGNORECASE)
            clause_num = clause_match.group(1) if clause_match else f"Sec-{chunk_idx+1}"
            
            chunk_id = f"{doc_name}_{chunk_idx}_{clause_num.replace(' ', '_')}"
            
            chunks.append({
                "id": chunk_id,
                "text": sec_clean,
                "metadata": {
                    "document_name": doc_name,
                    "document_type": doc_type,
                    "issuing_authority": authority,
                    "clause_number": clause_num,
                    "chunk_index": chunk_idx,
                    "char_count": len(sec_clean)
                }
            })
            chunk_idx += 1
            
        return chunks

    def process_and_index(self) -> Dict[str, Any]:
        doc_registry = [
            {
                "file": "DoE_OM_Startup_Relaxation_2016.txt",
                "title": "DoE OM F.20/2/2014-PPD(Pt.) Startup Relaxation",
                "type": "statutory_order",
                "authority": "Department of Expenditure, Ministry of Finance"
            },
            {
                "file": "GFR_2017_Chapter_6_Procurement.txt",
                "title": "General Financial Rules 2017 (Chapter 6 Procurement)",
                "type": "statutory_rules",
                "authority": "Ministry of Finance"
            },
            {
                "file": "MSE_Procurement_Policy_Order_2012.txt",
                "title": "Public Procurement Policy for MSEs Order 2012",
                "type": "statutory_order",
                "authority": "Ministry of MSME"
            },
            {
                "file": "NICSI_Tender_IT_Infra_8921.txt",
                "title": "NICSI IT Infrastructure Tender NICSI/PROC/2023/IT-INFRA-8921",
                "type": "tender",
                "authority": "National Informatics Centre Services Inc. (NICSI)"
            }
        ]

        total_chunks = 0
        manifest = []

        for doc_info in doc_registry:
            raw_path = os.path.join(RAW_DIR, doc_info["file"])
            if not os.path.exists(raw_path):
                print(f"Warning: File {raw_path} not found.")
                continue

            checksum = self.compute_sha256(raw_path)
            with open(raw_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            chunks = self.chunk_document(
                text_content, 
                doc_info["file"], 
                doc_info["type"], 
                doc_info["authority"]
            )
            
            # Save processed JSON
            processed_path = os.path.join(PROCESSED_DIR, f"{doc_info['file']}.json")
            with open(processed_path, "w", encoding="utf-8") as pf:
                json.dump({
                    "metadata": doc_info,
                    "sha256": checksum,
                    "chunk_count": len(chunks),
                    "chunks": chunks
                }, pf, indent=2)

            # Embed and upsert into ChromaDB
            ids = [c["id"] for c in chunks]
            texts = [c["text"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            
            embeddings = self.encoder.encode(texts, show_progress_bar=False).tolist()
            
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            total_chunks += len(chunks)
            manifest.append({
                "document": doc_info["title"],
                "filename": doc_info["file"],
                "type": doc_info["type"],
                "authority": doc_info["authority"],
                "checksum": checksum,
                "chunks": len(chunks)
            })
            print(f"Indexed: {doc_info['title']} ({len(chunks)} chunks)")

        summary = {
            "status": "success",
            "indexed_documents_count": len(manifest),
            "total_chunks_indexed": total_chunks,
            "index_freshness": datetime.utcnow().isoformat(),
            "documents": manifest
        }
        
        with open(os.path.join(PROCESSED_DIR, "index_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

if __name__ == "__main__":
    pipeline = CorpusIngestionPipeline()
    res = pipeline.process_and_index()
    print("Ingestion complete:", json.dumps(res, indent=2))
