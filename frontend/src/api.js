// Пока работаем без сервера.
// Формат запроса и ответа соответствует API Сони.

export async function sendChatMessage({ session_id, message }) {
  if (!session_id || !message.trim()) {
    throw new Error('Не указана сессия или сообщение')
  }

  return {
    answer: 'Это тестовый ответ backend.',
    sources: [],
  }
}