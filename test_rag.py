import chromadb
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer('BAAI/bge-m3')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="tender_knowledge_base",
    metadata={"hnsw:space": "cosine"}
)
# это пока типа тест данные
test_chunks = [
    "Для участия в тендере требуется банковская гарантия в размере 5% от суммы.",
    "Заявки на участие принимаются строго до 25 октября 2026 года до 18:00."
]

test_metadatas = [
    {"doc_id": "tender_01", "page": 4, "section": "3.1 Гарантии", "source": "инструкция.pdf"},
    {"doc_id": "tender_01", "page": 7, "section": "4.2 Сроки", "source": "инструкция.pdf"}
]

test_ids = ["chunk_001", "chunk_002"]

# в векторы + сейв
chunk_embeddings = embedder.encode(test_chunks, normalize_embeddings=True).tolist()

collection.add(
    documents=test_chunks,
    embeddings=chunk_embeddings,
    metadatas=test_metadatas,
    ids=test_ids
)

# поиск пров.
user_query = "Какая нужна гарантия?"
query_embedding = embedder.encode([user_query], normalize_embeddings=True).tolist()

search_results = collection.query(
    query_embeddings=query_embedding,
    n_results=1
)

print("\n Проверко")
print("Найденный текст:", search_results['documents'][0][0])
print("Метаданные:", search_results['metadatas'][0][0])
print("Расстояние (Cosine):", search_results['distances'][0][0])