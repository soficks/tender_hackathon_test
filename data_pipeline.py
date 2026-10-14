import pdfplumber
import re
import json
import os
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter

FILES = [
    "Инструкция по работе с машиночитаемыми доверенностями.pdf",
    "Инструкция по работе с Порталом для заказчика.pdf",
    "Инструкция по работе с Порталом для поставщика.pdf",
    "Инструкция по формированию YML.pdf",
    "Инструкция по электронному актированию.pdf"
]

def clean_text(text):
    if not text:
        return ""
    
    # Базовая очистка от колонтитулов и мусора
    text = re.sub(r'ПОРТАЛ ПОСТАВЩИКОВ МОСКВЫ.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'ИНСТРУКЦИЯ ПОСТАВЩИКА.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Рисунок\s*\d+\s*[-–].*?\n', '', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # Интеллектуальная склейка разорванных строк
    text = re.sub(r'(?<=[а-яА-Яa-zA-Z,])\n(?=[а-яА-Яa-zA-Z])', ' ', text)
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def process_pdf(file_path, stats):
    doc_name = os.path.basename(file_path)
    print(f"Парсинг: {doc_name}...")
    
    chunks_data = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    
    # Инициализация метрик для отчета
    stats[doc_name] = {'chunks': 0, 'chars': 0}
    seen_hashes = set()
    current_section = "" # Память текущего раздела
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                raw_text = page.extract_text()
                if not raw_text:
                    continue
                
                # Пропуск оглавлений
                if ("Содержание" in raw_text[:100] or "СОДЕРЖАНИЕ" in raw_text[:100]) and i < 6:
                    continue
                    
                cleaned_text = clean_text(raw_text)
                if len(cleaned_text) < 50: 
                    continue
                
                page_chunks = text_splitter.split_text(cleaned_text)
                
                for chunk_idx, chunk_text in enumerate(page_chunks):
                    # 1. ПУНКТ: Умное извлечение заголовков
                    # Ищем строки вида "1.1. Общие положения" или "ГЛАВА 2"
                    sec_match = re.search(r'(?m)^(\d+\.\d+\.?\s+[А-ЯA-Z].{3,60})$', chunk_text)
                    if sec_match:
                        current_section = sec_match.group(1).strip()
                        
                    # 2. ПУНКТ: Удаление 100% дубликатов (Хэширование)
                    chunk_hash = hashlib.md5(chunk_text.encode('utf-8')).hexdigest()
                    if chunk_hash in seen_hashes:
                        continue # Пропускаем дубликат
                    seen_hashes.add(chunk_hash)
                    
                    # Сборка финального чанка
                    chunks_data.append({
                        "chunk_id": f"{doc_name.replace('.pdf', '')}_p{i+1}_c{chunk_idx}",
                        "text": chunk_text,
                        "source_doc": doc_name,
                        "page": i + 1,
                        "section_title": current_section 
                    })
                    
                    # Сбор статистики
                    stats[doc_name]['chunks'] += 1
                    stats[doc_name]['chars'] += len(chunk_text)
                    
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
        
    return chunks_data

def main():
    all_data = []
    stats = {} # Словарь для хранения статистики качества
    
    for file in FILES:
        if os.path.exists(file):
            all_data.extend(process_pdf(file, stats))
        else:
            print(f"Предупреждение: Файл '{file}' не найден.")
            
    output_file = "rag_knowledge_base.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    # 3. ПУНКТ: Генерация красивого отчета о качестве
    print("\n" + "="*50)
    print("ОТЧЕТ О КАЧЕСТВЕ ДАННЫХ (DATA QUALITY REPORT)")
    print("="*50)
    
    total_chunks = len(all_data)
    if total_chunks > 0:
        total_chars = sum(s['chars'] for s in stats.values())
        print(f"Всего собрано уникальных чанков: {total_chunks}")
        print(f"Средняя длина чанка: {total_chars // total_chunks} символов\n")
        print("Детализация по документам:")
        for doc, data in stats.items():
            if data['chunks'] > 0:
                avg_len = data['chars'] // data['chunks']
                print(f"{doc[:35]:<35} | Чанков: {data['chunks']:<4} | Ср. длина: {avg_len} симв.")
    else:
        print("База пуста. Проверьте исходные файлы.")
        
    print("="*50)
    print(f"Датасет '{output_file}' готов! Можно отдавать ML-инженеру.")

if __name__ == "__main__":
    main()