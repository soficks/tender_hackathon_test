import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_PATH = BASE_DIR / "rag_knowledge_base.jsonl"
CHROMA_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "tender_knowledge_base"
MODEL_NAME = "BAAI/bge-m3"


class RagService:
    def __init__(self):
        self.embedder = SentenceTransformer(MODEL_NAME)

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        self._load_knowledge_base()

    def _load_knowledge_base(self):
        if not KNOWLEDGE_BASE_PATH.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {KNOWLEDGE_BASE_PATH}"
            )

        if self.collection.count() > 0:
            return

        documents = []
        metadatas = []
        ids = []

        with KNOWLEDGE_BASE_PATH.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:
                item = json.loads(line)

                documents.append(item["text"])

                metadatas.append({
                    "source_doc": item["source_doc"],
                    "page": item["page"],
                    "section_title": item["section_title"]
                })

                ids.append(item["chunk_id"])

        if not documents:
            raise ValueError(
                "Knowledge base is empty"
            )

        embeddings = self.embedder.encode(
            documents,
            normalize_embeddings=True,
            show_progress_bar=True
        ).tolist()

        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def search(
        self,
        query: str,
        top_k: int = 3
    ):
        query_embedding = self.embedder.encode(
            [query],
            normalize_embeddings=True
        ).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        return [
            {
                "text": document,
                "source": metadata,
                "distance": distance
            }
            for document, metadata, distance
            in zip(
                documents,
                metadatas,
                distances
            )
        ]


rag_service = None


def get_rag_service():
    global rag_service

    if rag_service is None:
        rag_service = RagService()

    return rag_service


def search_knowledge(
    query: str,
    top_k: int = 3
):
    return get_rag_service().search(
        query,
        top_k
    )