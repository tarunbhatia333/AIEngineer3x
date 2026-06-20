import React, { useRef, useState } from 'react';
import { validateSampleFile, parseSampleFile } from '../lib/files.js';

export default function FileDrop({ file, onChange, schema, onSchema }) {
  const inputRef = useRef(null);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);

  async function handleFile(f) {
    setError('');
    if (!f) {
      onChange(null);
      onSchema(null);
      return;
    }
    const err = validateSampleFile(f);
    if (err) {
      setError(err);
      return;
    }
    onChange(f);
    try {
      onSchema(await parseSampleFile(f));
    } catch {
      setError('Could not parse file');
    }
  }

  return (
    <div className="field">
      <span>Sample file (optional format reference — .csv or .xlsx)</span>
      <div
        className={`file-drop ${dragOver ? 'drag' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files?.[0]); }}
      >
        {file ? (
          <span>
            📄 {file.name} ({schema?.headers?.length || 0} columns detected)
          </span>
        ) : (
          <span>Drag &amp; drop a .csv/.xlsx sample here, or click to browse</span>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
      {error && <div className="error">⚠ {error}</div>}
      {file && (
        <button type="button" className="ghost" onClick={() => handleFile(null)}>
          Remove file
        </button>
      )}
    </div>
  );
}
