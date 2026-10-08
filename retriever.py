import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer

# Подключаемся к сохраненной базе и модели один раз при старте приложения
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="tenders")
embedder = SentenceTransformer('BAAI/bge-m3')

def get_relevant_context(user_query: str, top_k: int = 3) -> list[dict]:
    """
    Принимает вопрос пользователя, ищет релевантный контекст в ChromaDB
    и возвращает список чанков с метаданными.
    """
    # 1. Векторизуем вопрос
    query_embedding = embedder.encode([user_query]).tolist()
    
    # 2. Ищем top_k ближайших векторов
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    
    formatted_results = []
    
    # 3. Форматируем результат в удобный для Бэка список словарей
    for i in range(len(results["documents"][0])):
        formatted_results.append({
            "text": results["documents"][0][i],
            "source_doc": results["metadatas"][0][i].get("source_doc", ""),
            "page": results["metadatas"][0][i].get("page", 0),
            "section_title": results["metadatas"][0][i].get("section_title", "")
        })
        
    return formatted_results

# Проверка работы функции
if __name__ == "__main__":
    context = get_relevant_context("Как добавить МЧД?", top_k=2)
    print("Функция работает! Возвращен контекст:")
    print(context)