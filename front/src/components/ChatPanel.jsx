import { useState } from "react";
import { chatQuery } from "../api/client";

function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userMsg = { role: "user", text: question };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      const data = await chatQuery(question);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          sql: data.sql,
          rows: data.rows,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="chat-empty">
            Ask anything about the FFXIV market — prices, trends, arbitrage
            opportunities, what's selling fast...
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            <div className="msg-text">{msg.text}</div>
            {msg.sql && (
              <details className="msg-sql">
                <summary>SQL ({msg.rows} rows)</summary>
                <pre>{msg.sql}</pre>
              </details>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-msg assistant">
            <div className="msg-text loading">Querying the market board...</div>
          </div>
        )}
      </div>

      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What are the cheapest HQ weapons on Jenova?"
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          Ask
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;
