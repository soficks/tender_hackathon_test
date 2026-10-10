import os
import json
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

# Отключаем сетевые проверки Hugging Face, чтобы убрать таймауты
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_PATH = BASE_DIR / "rag_knowledge_base.jsonl"
CHROMA_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "tender_knowledge_base"
MODEL_NAME = "BAAI/bge-m3"


class RagService:
    def __init__(self):
        # Модель инициализируется быстро только для поиска по 1 вопросу
        self.embedder = SentenceTransformer(MODEL_NAME)

        # Подключаемся к уже готовой базе
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
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

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        return [
            {
                "text": document,
                "source": metadata,
                "distance": distance
            }
            for document, metadata, distance
            in zip(documents, metadatas, distances)
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