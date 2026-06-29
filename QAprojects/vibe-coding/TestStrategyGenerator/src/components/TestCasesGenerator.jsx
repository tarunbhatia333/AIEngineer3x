import React, { useState } from 'react';
import { generateTestCases, saveFiles } from '../lib/api.js';
import { toCsvBlob, toXlsxBlob, downloadBlob } from '../lib/files.js';
import TicketSourceToggle from './TicketSourceToggle.jsx';
import FileDrop from './FileDrop.jsx';
import TestCasesView from './TestCasesView.jsx';

export default function TestCasesGenerator({
  config, envStatus, goSettings, goPicker,
  dataSource, onDataSourceChange, ticketId, onTicketIdChange, onGenerated, onUseForScripts,
}) {
  const [file, setFile] = useState(null);
  const [schema, setSchema] = useState(null);
  const [count, setCount] = useState(8);
  const [platform, setPlatform] = useState('Web');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [savedPath, setSavedPath] = useState('');

  const hasLlmKey = Boolean(envStatus?.providers?.[envStatus?.activeProvider] || config?.llm?.[config?.llm?.active]?.key);
  const ready = Boolean(ticketId.trim() && hasLlmKey);

  async function onGenerate(e) {
    e.preventDefault();
    setError('');
    setResult(null);
    setSavedPath('');
    setLoading(true);
    try {
      const data = await generateTestCases(
        ticketId.trim(),
        { ...config, dataSource },
        schema,
        { count: Number(count) || 8, platform, notes },
      );
      setResult(data);
      onGenerated(ticketId.trim(), data.columns, data.testCases);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function download(format) {
    const blob = format === 'xlsx' ? toXlsxBlob(result.columns, result.testCases) : toCsvBlob(result.columns, result.testCases);
    downloadBlob(blob, `test-cases-${ticketId.trim()}.${format}`);
  }

  async function saveServer() {
    setError('');
    try {
      const blob = await toCsvBlob(result.columns, result.testCases).text();
      const r = await saveFiles([{ filename: `test-cases-${ticketId.trim()}.csv`, content: blob }]);
      setSavedPath(r.path);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="card">
      <div className="plan-head">
        <h2>Generate Test Cases</h2>
        <button className="link" onClick={goPicker}>Change mode</button>
      </div>

      {!hasLlmKey && (
        <div className="warn">
          Missing LLM credentials. <button className="link" onClick={goSettings}>Open Settings</button>
        </div>
      )}

      <form onSubmit={onGenerate} className="form">
        <TicketSourceToggle
          dataSource={dataSource}
          onDataSourceChange={onDataSourceChange}
          ticketId={ticketId}
          onTicketIdChange={onTicketIdChange}
        />

        <FileDrop file={file} onChange={setFile} schema={schema} onSchema={setSchema} />

        <div className="row-fields">
          <label className="field">
            <span>Number of test cases</span>
            <input type="number" min="1" max="50" value={count} onChange={(e) => setCount(e.target.value)} />
          </label>
          <label className="field">
            <span>Platform</span>
            <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
              <option>Web</option>
              <option>Mobile</option>
              <option>Both</option>
            </select>
          </label>
        </div>
        <label className="field">
          <span>Notes (optional)</span>
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. focus on negative test cases, include accessibility checks"
          />
        </label>

        <div className="row">
          <button type="submit" className="primary" disabled={loading || !ready}>
            {loading ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </form>

      {loading && <div className="loader">Fetching ticket + asking the LLM…</div>}
      {error && <div className="error">⚠ {error}</div>}

      {result && (
        <>
          <div className="actions">
            <button onClick={() => download('csv')} className="ghost">⬇ Download .csv</button>
            <button onClick={() => download('xlsx')} className="ghost">⬇ Download .xlsx</button>
            <button onClick={saveServer} className="ghost">💾 Save to server</button>
            <button onClick={onUseForScripts} className="ghost">
              ➜ Use these test cases
            </button>
            {savedPath && <span className="ok">Saved → <code>{savedPath}</code></span>}
          </div>
          <TestCasesView
            columns={result.columns}
            testCases={result.testCases}
            onChange={(testCases) => setResult((r) => ({ ...r, testCases }))}
          />
        </>
      )}
    </section>
  );
}
