import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

SYSTEM_PROMPT = """Ты — официальный ИИ-консультант Портала поставщиков.
Твоя задача — точно отвечать на вопросы пользователя ИСКЛЮЧИТЕЛЬНО на основе переданного контекста.

Правила:
1. Используй только факты из контекста. Не придумывай ничего от себя.
2. Если в контексте нет прямого ответа на вопрос пользователя, ответь ровно так: 
"К сожалению, в базе знаний нет информации по данному вопросу. Перевожу ваш запрос на оператора."
3. Отвечай кратко, чётко и по делу.
"""

def generate_answer(query: str, context: list) -> str:
    if not context:
        return "К сожалению, в базе знаний нет информации по данному вопросу. Перевожу ваш запрос на оператора."

    # Собираем фрагменты в сплошной текст для промпта
    context_blocks = []
    for item in context:
        # Извлекаем текст чанка
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        context_blocks.append(text)
    
    context_text = "\n\n---\n\n".join(context_blocks)

    prompt = f"Контекст:\n{context_text}\n\nВопрос: {query}\n\nОтвет:"

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "system": SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return "Ошибка: Ollama не запущена. Запустите модель через 'ollama run qwen2.5:3b' в консоли."
    except Exception as e:
        return f"Ошибка при генерации: {str(e)}"