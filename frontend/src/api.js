
const API_URL = 'http://localhost:8000'

export async function sendChatMessage({ session_id, message }) {
  if (!session_id || !message.trim()) {
    throw new Error('Не указана сессия или сообщение')
  }

  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id,
      message,
    }),
  })

  if (!response.ok) {
    throw new Error(`Ошибка сервера: ${response.status}`)
  }

  return await response.json()
}
