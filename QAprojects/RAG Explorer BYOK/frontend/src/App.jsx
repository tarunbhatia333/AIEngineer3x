import { useEffect, useRef, useState } from "react";
import PipelineStepper from "./components/PipelineStepper.jsx";
import UploadPanel from "./components/UploadPanel.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import SettingsPage from "./components/SettingsPage.jsx";
import ThemeSwitcher from "./components/ThemeSwitcher.jsx";
import { hasAllKeys } from "./keys.js";
import {
  getCollections,
  activateCollection,
  deleteCollection,
  reingestDefault,
  uploadDocument,
  runQuery,
} from "./api.js";

let turnId = 0;
const THEME_STORAGE_KEY = "rag-explorer-theme";

export default function App() {
  const [view, setView] = useState("app");
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_STORAGE_KEY) || "blue");
  const [keysReady, setKeysReady] = useState(hasAllKeys());
  const [collections, setCollections] = useState([]);
  const [activeCollection, setActiveCollection] = useState("default");
  const [history, setHistory] = useState([]);
  const [busyQuery, setBusyQuery] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState("");
  const [activeStage, setActiveStage] = useState(null);
  const [doneStages, setDoneStages] = useState([]);
  const resetTimer = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.accent = theme;
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const refreshCollections = async () => {
    if (!hasAllKeys()) return;
    try {
      const data = await getCollections();
      setCollections(data.collections);
      setActiveCollection(data.active);
    } catch {
      // backend not up yet, or keys are invalid; ignore, UI will show empty state
    }
  };

  useEffect(() => {
    refreshCollections();
  }, []);

  const handleKeysChanged = () => {
    setKeysReady(hasAllKeys());
    refreshCollections();
  };

  const animateStages = async (stageKeys, promise, stepMs = 450) => {
    if (resetTimer.current) clearTimeout(resetTimer.current);
    let index = -1;
    const interval = setInterval(() => {
      index++;
      if (index < stageKeys.length) {
        setActiveStage(stageKeys[index]);
        setDoneStages(stageKeys.slice(0, index));
      } else {
        clearInterval(interval);
      }
    }, stepMs);

    try {
      const result = await promise;
      clearInterval(interval);
      setDoneStages(stageKeys);
      setActiveStage(null);
      return result;
    } catch (err) {
      clearInterval(interval);
      setActiveStage(null);
      setDoneStages([]);
      throw err;
    } finally {
      resetTimer.current = setTimeout(() => setDoneStages([]), 1500);
    }
  };

  const handleUpload = async (file) => {
    setIngesting(true);
    setIngestStatus(`Ingesting ${file.name}...`);
    try {
      const result = await animateStages(["source", "chunk", "embed", "store"], uploadDocument(file));
      setIngestStatus(`Ingested ${result.chunk_count} chunks from ${result.source}`);
      await refreshCollections();
    } catch (err) {
      setIngestStatus(`Ingestion failed: ${err.message}`);
    } finally {
      setIngesting(false);
    }
  };

  const handleReingestDefault = async () => {
    setIngesting(true);
    setIngestStatus("Re-ingesting default PDF...");
    try {
      const result = await animateStages(["source", "chunk", "embed", "store"], reingestDefault());
      setIngestStatus(`Ingested ${result.chunk_count} chunks from ${result.source}`);
      await refreshCollections();
    } catch (err) {
      setIngestStatus(`Ingestion failed: ${err.message}`);
    } finally {
      setIngesting(false);
    }
  };

  const handleActivate = async (name) => {
    await activateCollection(name);
    await refreshCollections();
  };

  const handleDelete = async (name) => {
    await deleteCollection(name);
    await refreshCollections();
  };

  const handleAsk = async (question) => {
    setBusyQuery(true);
    const id = ++turnId;
    try {
      const result = await animateStages(["embed", "retrieve", "llm"], runQuery(question, activeCollection));
      setHistory((h) => [...h, { id, question, chunks: result.chunks, answer: result.answer }]);
    } catch (err) {
      setHistory((h) => [...h, { id, question, chunks: [], error: err.message }]);
    } finally {
      setBusyQuery(false);
    }
  };

  const activeMeta = collections.find((c) => c.name === activeCollection);

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-top">
          <div>
            <h1>RAG Explorer</h1>
            <p className="subtitle">PDF → Chunking → Embedding → Vector Store → Retrieval → LLM Answer</p>
          </div>
          <div className="app-header-actions">
            <ThemeSwitcher theme={theme} onChange={setTheme} />
            <button className="btn-small" onClick={() => setView(view === "settings" ? "app" : "settings")}>
              {view === "settings" ? "← Back" : "⚙ Settings"}
            </button>
          </div>
        </div>
      </header>

      {view === "settings" ? (
        <SettingsPage onBack={() => setView("app")} onSaved={handleKeysChanged} />
      ) : (
        <>
          {!keysReady && (
            <div className="key-banner">
              This app brings your own API keys — nothing is stored on the server.{" "}
              <button className="link-button" onClick={() => setView("settings")}>
                Add your Groq, OpenAI, and Pinecone keys in Settings
              </button>{" "}
              to start ingesting and asking questions.
            </div>
          )}

          <PipelineStepper activeStage={activeStage} doneStages={doneStages} />

          <main className="app-main">
            <UploadPanel
              collections={collections}
              activeCollection={activeCollection}
              onActivate={handleActivate}
              onDelete={handleDelete}
              onUpload={handleUpload}
              onReingestDefault={handleReingestDefault}
              ingesting={ingesting}
              ingestStatus={ingestStatus}
              disabled={!keysReady}
            />
            <ChatPanel
              onAsk={handleAsk}
              busy={busyQuery}
              history={history}
              activeCollection={activeCollection}
              activeLabel={activeMeta?.label}
              disabled={!keysReady}
            />
          </main>
        </>
      )}
    </div>
  );
}
