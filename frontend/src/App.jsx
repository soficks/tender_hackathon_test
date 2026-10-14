import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { sendChatMessage } from './api'
import './App.css'

const money = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 2,
})

function getSessionId() {
  const key = 'hackathon-session-id'
  let sessionId = localStorage.getItem(key)

  if (!sessionId) {
    sessionId = crypto.randomUUID()
    localStorage.setItem(key, sessionId)
  }

  return sessionId
}

function createWelcomeMessage() {
  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: 'Здравствуйте! Чем могу помочь?',
  }
}

function CreditCalculator() {
  const [amount, setAmount] = useState('100000')
  const [months, setMonths] = useState('12')
  const [rate, setRate] = useState('18')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  function updateField(setter, value) {
    setter(value)
    setResult(null)
    setError('')
  }

  function calculate(event) {
    event.preventDefault()
    setResult(null)
    setError('')

    if (
      amount.trim() === '' ||
      months.trim() === '' ||
      rate.trim() === ''
    ) {
      setError('Заполните все поля.')
      return
    }

    const principal = Number(amount)
    const duration = Number(months)
    const annualRate = Number(rate)

    if (
      !Number.isFinite(principal) ||
      principal <= 0 ||
      principal > 1000000000
    ) {
      setError('Введите сумму больше 0 и не больше 1 млрд ₽.')
      return
    }

    if (
      !Number.isInteger(duration) ||
      duration < 1 ||
      duration > 600
    ) {
      setError('Введите целый срок от 1 до 600 месяцев.')
      return
    }

    if (
      !Number.isFinite(annualRate) ||
      annualRate < 0 ||
      annualRate > 100
    ) {
      setError('Введите годовую ставку от 0 до 100%.')
      return
    }

    const monthlyRate = annualRate / 100 / 12

    const payment =
      monthlyRate === 0
        ? principal / duration
        : (principal * monthlyRate) /
          -Math.expm1(-duration * Math.log1p(monthlyRate))

    const total = payment * duration
    const overpayment = Math.max(0, total - principal)

    setResult({
      payment,
      total,
      overpayment,
    })
  }

  return (
    <div className="calculator-card">
      <h2>Кредитный калькулятор</h2>

      <p className="calculator-note">
        Начальные значения — тестовый пример. Введите свои данные.
      </p>

      <form className="calculator-form" onSubmit={calculate}>
        <label>
          Сумма кредита, ₽
          <input
            type="number"
            min="0.01"
            max="1000000000"
            step="0.01"
            required
            value={amount}
            onChange={(event) =>
              updateField(setAmount, event.target.value)
            }
          />
        </label>

        <label>
          Срок, месяцев
          <input
            type="number"
            min="1"
            max="600"
            step="1"
            required
            value={months}
            onChange={(event) =>
              updateField(setMonths, event.target.value)
            }
          />
        </label>

        <label>
          Годовая ставка, %
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            required
            value={rate}
            onChange={(event) =>
              updateField(setRate, event.target.value)
            }
          />
        </label>

        <button type="submit" className="product-button">
          Рассчитать
        </button>
      </form>

      {error && (
        <p className="calculator-error" role="alert">
          {error}
        </p>
      )}

      {result && (
        <div className="calculator-result" aria-live="polite">
          <dl className="product-details">
            <div>
              <dt>Ежемесячный платёж</dt>
              <dd>{money.format(result.payment)}</dd>
            </div>

            <div>
              <dt>Общая сумма выплат</dt>
              <dd>{money.format(result.total)}</dd>
            </div>

            <div>
              <dt>Переплата по процентам</dt>
              <dd>{money.format(result.overpayment)}</dd>
            </div>
          </dl>
        </div>
      )}

      <p className="calculator-note">
        Предварительный расчёт с равными ежемесячными платежами,
        без комиссий и страховки. Фактический график банка может
        отличаться из-за дат платежей и округления.
      </p>
    </div>
  )
}

function App() {
  const [sessionId] = useState(getSessionId)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState(() => [
    createWelcomeMessage(),
  ])

  const messagesEnd = useRef(null)
  const sending = useRef(false)

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  function addAssistantMessage(content, card = null) {
    setMessages((previous) => [
      ...previous,
      {
        id: crypto.randomUUID(),
        role: 'assistant',
        content,
        card,
      },
    ])
  }

  async function sendMessage(text) {
    const question = text.trim()

    if (!question || sending.current) return

    setMessages((previous) => [
      ...previous,
      {
        id: crypto.randomUUID(),
        role: 'user',
        content: question,
      },
    ])

    setInput('')

    if (question === 'Рассчитать кредит') {
      addAssistantMessage(
        'Укажите сумму, срок и годовую ставку:',
        { type: 'calculator' },
      )
      return
    }

    if (question === 'Ключевые условия') {
      addAssistantMessage(
        'Вот пример карточки кредитного продукта. **Условия тестовые и не являются предложением банка.**',
        {
          type: 'product',
          title: 'Кредит — демонстрационный пример',
          rate: '18% годовых',
          amount: '100 000 ₽',
          term: '12 месяцев',
        },
      )
      return
    }

    if (question === 'Оформить кредит') {
      addAssistantMessage(
        'Оформление пока недоступно в тестовом режиме. Заявка не создана.',
        {
          type: 'status',
          title: 'Оформление кредита',
          status: 'Сервис оформления ещё не подключён',
        },
      )
      return
    }

    if (question === 'Перевести на оператора') {
      addAssistantMessage(
        'Это тестовый режим. Подключение оператора пока недоступно.',
        {
          type: 'status',
          title: 'Обращение к оператору',
          status: 'Недоступно в тестовом режиме',
        },
      )
      return
    }

    sending.current = true
    setIsLoading(true)

    try {
      const response = await sendChatMessage({
        session_id: sessionId,
        message: question,
      })

      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
        },
      ])
    } catch (error) {
      console.error('Ошибка получения ответа:', error)

      addAssistantMessage(
        'Не удалось получить ответ. Попробуйте отправить сообщение ещё раз.',
      )
    } finally {
      sending.current = false
      setIsLoading(false)
    }
  }

  function resetChat() {
    if (sending.current) return

    setInput('')
    setMessages([createWelcomeMessage()])
  }

  function handleSubmit(event) {
    event.preventDefault()
    sendMessage(input)
  }

  return (
    <main className="chat">
      <header className="chat-header">
        <div>
          <h1>ИИ-консультант</h1>
          <p>Тестовый режим · Бэкенд ещё не подключён</p>
        </div>

        <button
          type="button"
          className="reset-button"
          onClick={resetChat}
          disabled={isLoading}
        >
          Новый диалог
        </button>
      </header>

      <section
        className="messages"
        aria-label="Сообщения"
        aria-live="polite"
      >
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message message-${message.role}`}
          >
            {message.role === 'assistant' ? (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            ) : (
              message.content
            )}

            {message.sources?.length > 0 && (
              <div className="sources">
                <strong>Источники:</strong>
                <ul>
                  {message.sources.map((source, index) => (
                    <li key={`${source}-${index}`}>{source}</li>
                  ))}
                </ul>
              </div>
            )}

            {message.card?.type === 'calculator' && (
              <CreditCalculator />
            )}

            {message.card?.type === 'status' && (
              <div className="status-card">
                <strong>{message.card.title}</strong>
                <span>{message.card.status}</span>
              </div>
            )}

            {message.card?.type === 'product' && (
              <div className="product-card">
                <span className="product-badge">
                  Тестовые условия
                </span>

                <h2>{message.card.title}</h2>

                <dl className="product-details">
                  <div>
                    <dt>Годовая ставка</dt>
                    <dd>{message.card.rate}</dd>
                  </div>
                  <div>
                    <dt>Сумма кредита</dt>
                    <dd>{message.card.amount}</dd>
                  </div>
                  <div>
                    <dt>Срок</dt>
                    <dd>{message.card.term}</dd>
                  </div>
                </dl>

                <button
                  type="button"
                  className="product-button"
                  disabled={isLoading}
                  onClick={() => sendMessage('Оформить кредит')}
                >
                  Оформить
                </button>

                <p className="product-note">
                  Демонстрационная карточка. Реальные условия
                  появятся после подключения данных продукта.
                </p>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="message message-assistant">
            Ассистент готовит ответ…
          </div>
        )}

        <div ref={messagesEnd} />
      </section>

      <footer className="chat-footer">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            aria-label="Ваш вопрос"
            placeholder="Напишите ваш вопрос..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
          >
            {isLoading ? 'Ожидание…' : 'Отправить'}
          </button>
        </form>

        <div className="quick-replies">
          {[
            'Ключевые условия',
            'Рассчитать кредит',
            'Перевести на оператора',
          ].map((label) => (
            <button
              key={label}
              type="button"
              disabled={isLoading}
              onClick={() => sendMessage(label)}
            >
              {label}
            </button>
          ))}
        </div>
      </footer>
    </main>
  )
}

export default App