import { useState } from "react";
import { getKeys, saveKeys, clearKeys } from "../keys.js";

const FIELDS = [
  {
    key: "groq",
    label: "Groq API Key",
    placeholder: "gsk_...",
    href: "https://console.groq.com/keys",
    hint: "Used to generate the final answer.",
  },
  {
    key: "openai",
    label: "OpenAI API Key",
    placeholder: "sk-...",
    href: "https://platform.openai.com/api-keys",
    hint: "Used to embed your documents and questions.",
  },
  {
    key: "pinecone",
    label: "Pinecone API Key",
    placeholder: "pcsk_...",
    href: "https://app.pinecone.io",
    hint: "Used as the vector store. An index is created automatically the first time you ingest something.",
  },
];

export default function SettingsPage({ onBack, onSaved }) {
  const [values, setValues] = useState(getKeys());
  const [status, setStatus] = useState("");

  const update = (key, value) => setValues((v) => ({ ...v, [key]: value }));

  const handleSave = (e) => {
    e.preventDefault();
    saveKeys(values);
    setStatus("Saved — your keys are stored only in this browser.");
    onSaved?.();
  };

  const handleClear = () => {
    clearKeys();
    setValues({ groq: "", openai: "", pinecone: "" });
    setStatus("Cleared all keys from this browser.");
    onSaved?.();
  };

  return (
    <div className="panel settings-panel">
      <div className="settings-header">
        <h2>Settings</h2>
        <button className="btn-small" onClick={onBack}>
          ← Back
        </button>
      </div>

      <p className="muted settings-note">
        Your keys are stored only in this browser's local storage and sent directly
        to the API with each request — they are never saved on the server.
      </p>

      <form className="settings-form" onSubmit={handleSave}>
        {FIELDS.map((f) => (
          <label key={f.key} className="settings-field">
            <span className="settings-label">
              {f.label}
              <a href={f.href} target="_blank" rel="noreferrer">
                get a key
              </a>
            </span>
            <input
              type="password"
              autoComplete="off"
              spellCheck={false}
              placeholder={f.placeholder}
              value={values[f.key]}
              onChange={(e) => update(f.key, e.target.value)}
            />
            <span className="settings-hint">{f.hint}</span>
          </label>
        ))}

        <div className="settings-actions">
          <button type="submit" className="btn-primary">
            Save keys
          </button>
          <button type="button" className="btn-secondary" onClick={handleClear}>
            Clear all
          </button>
        </div>
        {status && <div className="status">{status}</div>}
      </form>
    </div>
  );
}
