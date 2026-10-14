import chromadb
from sentence_transformers import SentenceTransformer

# 1. Подключаемся к той же базе на диске
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="tenders")

# 2. Загружаем ту же модель для векторизации ВОПРОСА
embedder = SentenceTransformer('BAAI/bge-m3')

# 3. Тестовый вопрос
user_query = "Как добавить МЧД в профиль?"

# 4. Превращаем вопрос в вектор
query_embedding = embedder.encode([user_query]).tolist()

# 5. Ищем 2 самых близких чанка по косинусному расстоянию
results = collection.query(
    query_embeddings=query_embedding,
    n_results=2
)

# 6. Выводим результат
print("\n--- НАЙДЕННЫЙ КОНТЕКСТ ---")
for i in range(len(results["documents"][0])):
    print(f"\nРезультат #{i+1}:")
    print(f"Документ: {results['metadatas'][0][i]['source_doc']}")
    print(f"Страница: {results['metadatas'][0][i]['page']}")
    print(f"Раздел: {results['metadatas'][0][i]['section_title']}")
    print(f"Текст чанка: {results['documents'][0][i][:150]}...")