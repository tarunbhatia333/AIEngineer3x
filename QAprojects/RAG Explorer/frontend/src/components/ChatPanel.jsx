import { useState } from "react";
import RetrievedChunks from "./RetrievedChunks.jsx";
import AnswerPanel from "./AnswerPanel.jsx";

export default function ChatPanel({ onAsk, busy, history, activeCollection, activeLabel }) {
  const [question, setQuestion] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || busy) return;
    onAsk(q);
    setQuestion("");
  };

  return (
    <div className="panel chat-panel">
      <h2>Ask a Question</h2>
      <div className="active-collection-note">
        Querying: <strong>{activeLabel || activeCollection}</strong>
      </div>

      <form className="chat-form" onSubmit={submit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask something about the active document..."
          disabled={busy}
        />
        <button type="submit" disabled={busy || !question.trim()}>
          {busy ? "Thinking..." : "Ask"}
        </button>
      </form>

      <div className="chat-history">
        {history.length === 0 && <p className="muted">No questions yet — ask something above.</p>}
        {history
          .slice()
          .reverse()
          .map((turn) => (
            <div key={turn.id} className="chat-turn">
              <div className="chat-question">Q: {turn.question}</div>
              <RetrievedChunks chunks={turn.chunks} />
              <AnswerPanel answer={turn.answer} error={turn.error} />
            </div>
          ))}
      </div>
    </div>
  );
}
