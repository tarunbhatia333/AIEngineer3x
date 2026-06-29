import React, { useEffect, useState } from 'react';
import { generateTestScripts, saveFiles } from '../lib/api.js';
import { parseFullFile, validateSampleFile } from '../lib/files.js';
import TestScriptsView from './TestScriptsView.jsx';

function relativeTime(iso) {
  const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return 'just now';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return `${hours} hr ago`;
}

export default function TestScriptsGenerator({ config, envStatus, goSettings, goPicker, testCaseHistory }) {
  const [source, setSource] = useState(testCaseHistory.length ? 'generated' : 'paste');
  const [selectedId, setSelectedId] = useState(testCaseHistory[0]?.id);
  const [uploaded, setUploaded] = useState(null);
  const [pasted, setPasted] = useState('');
  const [browser, setBrowser] = useState('Chrome');
  const [framework, setFramework] = useState('pytest');
  const [pageObjectModel, setPageObjectModel] = useState(false);
  const [baseUrl, setBaseUrl] = useState('');
  const [oneFile, setOneFile] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [files, setFiles] = useState(null);
  const [warnings, setWarnings] = useState(null);
  const [savedPath, setSavedPath] = useState('');

  const hasLlmKey = Boolean(envStatus?.providers?.[envStatus?.activeProvider] || config?.llm?.[config?.llm?.active]?.key);
  const selectedEntry = testCaseHistory.find((h) => h.id === selectedId);

  // Keep the selection valid if history changes (e.g. a fresh batch arrives while this mode is open).
  useEffect(() => {
    if (!testCaseHistory.find((h) => h.id === selectedId)) {
      setSelectedId(testCaseHistory[0]?.id);
    }
  }, [testCaseHistory]);

  async function handleUpload(file) {
    setError('');
    const err = validateSampleFile(file);
    if (err) return setError(err);
    try {
      const { rows } = await parseFullFile(file);
      setUploaded(rows);
    } catch {
      setError('Could not parse file');
    }
  }

  function testCasesPayload() {
    if (source === 'generated') return selectedEntry?.testCases || [];
    if (source === 'upload') return uploaded || [];
    return pasted;
  }

  const ready = Boolean(
    hasLlmKey &&
      ((source === 'generated' && selectedEntry?.testCases?.length) ||
        (source === 'upload' && uploaded?.length) ||
        (source === 'paste' && pasted.trim())),
  );

  async function onGenerate(e) {
    e.preventDefault();
    setError('');
    setFiles(null);
    setWarnings(null);
    setSavedPath('');
    setLoading(true);
    try {
      const data = await generateTestScripts(testCasesPayload(), config, {
        browser,
        framework,
        pageObjectModel,
        baseUrl,
        oneFile,
      });
      setFiles(data.files);
      setWarnings(data.errors || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function saveServer() {
    setError('');
    try {
      const r = await saveFiles(files);
      setSavedPath(r.path);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="card">
      <div className="plan-head">
        <h2>Generate Test Scripts</h2>
        <button className="link" onClick={goPicker}>Change mode</button>
      </div>

      {!hasLlmKey && (
        <div className="warn">
          Missing LLM credentials. <button className="link" onClick={goSettings}>Open Settings</button>
        </div>
      )}

      <form onSubmit={onGenerate} className="form">
        <div className="field">
          <span>Test cases source</span>
          <div className="source-pills">
            <button type="button" className={source === 'generated' ? 'active' : ''} onClick={() => setSource('generated')}>
              Use generated
            </button>
            <button type="button" className={source === 'upload' ? 'active' : ''} onClick={() => setSource('upload')}>
              Upload file
            </button>
            <button type="button" className={source === 'paste' ? 'active' : ''} onClick={() => setSource('paste')}>
              Paste text
            </button>
          </div>
        </div>

        {source === 'generated' && (
          testCaseHistory.length ? (
            <div className="field">
              <span>Last {testCaseHistory.length} generated batch(es) — pick one</span>
              <div className="history-list">
                {testCaseHistory.map((h) => (
                  <button
                    type="button"
                    key={h.id}
                    className={`history-card ${selectedId === h.id ? 'active' : ''}`}
                    onClick={() => setSelectedId(h.id)}
                  >
                    <strong>{h.ticketId}</strong>
                    <span>{h.testCases.length} test case(s) · {relativeTime(h.generatedAt)}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <p className="warn">No test cases generated yet — switch to Test Cases mode and generate some, or pick another source.</p>
          )
        )}

        {source === 'upload' && (
          <div className="field">
            <span>Upload test cases (.csv or .xlsx)</span>
            <input type="file" accept=".csv,.xlsx" onChange={(e) => handleUpload(e.target.files?.[0])} />
            {uploaded && <p className="muted">{uploaded.length} row(s) loaded.</p>}
          </div>
        )}

        {source === 'paste' && (
          <label className="field">
            <span>Paste test cases</span>
            <textarea
              rows={6}
              value={pasted}
              onChange={(e) => setPasted(e.target.value)}
              placeholder="Paste test case text here…"
            />
          </label>
        )}

        <div className="row-fields">
          <label className="field">
            <span>Browser</span>
            <select value={browser} onChange={(e) => setBrowser(e.target.value)}>
              <option>Chrome</option>
              <option>Firefox</option>
              <option>Edge</option>
            </select>
          </label>
          <label className="field">
            <span>Framework</span>
            <select value={framework} onChange={(e) => setFramework(e.target.value)}>
              <option value="pytest">pytest (Python)</option>
              <option value="unittest">unittest (Python)</option>
              <option value="testng">TestNG (Java)</option>
            </select>
          </label>
        </div>
        <div className="row-fields">
          <label className="field">
            <span>Base URL / environment</span>
            <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="https://staging.example.com" />
          </label>
          <label className="field checkbox-field">
            <span>Page Object Model</span>
            <input type="checkbox" checked={pageObjectModel} onChange={(e) => setPageObjectModel(e.target.checked)} />
          </label>
          <label className="field checkbox-field">
            <span>One consolidated file</span>
            <input type="checkbox" checked={oneFile} onChange={(e) => setOneFile(e.target.checked)} />
          </label>
        </div>

        <div className="row">
          <button type="submit" className="primary" disabled={loading || !ready}>
            {loading ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </form>

      {loading && <div className="loader">Asking the LLM for automation scripts…</div>}
      {error && <div className="error">⚠ {error}</div>}

      {warnings && (
        <div className="warn">
          {files.length} of {files.length + warnings.length} script(s) generated. Failed: {warnings.join('; ')}
        </div>
      )}

      {files && (
        <>
          <div className="actions">
            <button onClick={saveServer} className="ghost">💾 Save to server</button>
            {savedPath && <span className="ok">Saved → <code>{savedPath}</code></span>}
          </div>
          <TestScriptsView files={files} />
        </>
      )}
    </section>
  );
}
