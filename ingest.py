import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

def main():
    # ------------------------------------------------------------------
    # ШАГ 1: Подключение к базе и загрузка нейросети
    # ------------------------------------------------------------------
    # PersistentClient сохраняет базу на диск в папку ./chroma_db, 
    # чтобы данные не терялись при перезапуске
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Создаём или подключаемся к коллекции 'tenders'
    # hnsw:space: cosine означает, что близость векторов ищется по косинусному расстоянию
    collection = client.get_or_create_collection(
        name="tenders", 
        metadata={"hnsw:space": "cosine"}
    )
    
    # Загружаем эмбеддер BAAI/bge-m3 для перевода текста в векторы
    print("Загрузка модели BAAI/bge-m3...")
    embedder = SentenceTransformer('BAAI/bge-m3')

    # ------------------------------------------------------------------
    # ШАГ 2: Чтение файла от Саши и парсинг данных
    # ------------------------------------------------------------------
    file_path = "rag_knowledge_base.jsonl"
    if not os.path.exists(file_path):
        file_path = "rag_knowledge_base.json"  # Фолбэк, если файл назван без 'l'

    print(f"Чтение данных из {file_path}...")
    chunks = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Очищаем возможные маркеры списков (- )
            if line.startswith("- "):
                line = line[2:]
            if line:
                chunks.append(json.loads(line))

    # Разбираем прочитанный массив на 3 параллельных списка для ChromaDB
    ids = []
    documents = []
    metadatas = []

    for idx, item in enumerate(chunks):
        # 1. ID чанка
        chunk_id = str(item.get("chunk_id", f"chunk_{idx}"))
        
        # 2. Текст чанка (из него строится вектор)
        text = item.get("text", "")
        
        # 3. Метаданные (привязываются к вектору, но не участвуют в поиске)
        metadata = {
            "source_doc": str(item.get("source_doc", "")),
            "page": int(item.get("page", 0)),
            "section_title": str(item.get("section_title", ""))
        }

        ids.append(chunk_id)
        documents.append(text)
        metadatas.append(metadata)

    # ------------------------------------------------------------------
    # ШАГ 3: Генерация векторов (Эмбеддингов)
    # ------------------------------------------------------------------
    print(f"Генерация эмбеддингов для {len(documents)} чанков...")
    # encode превращает список текстов в список векторных массивов
    embeddings = embedder.encode(documents, show_progress_bar=True).tolist()

    # ------------------------------------------------------------------
    # ШАГ 4: Сохранение всего в ChromaDB
    # ------------------------------------------------------------------
    print("Запись данных в ChromaDB...")
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

    print("🎉 Данные успешно векторизованы и сохранены на диск!")

if __name__ == "__main__":
    main()