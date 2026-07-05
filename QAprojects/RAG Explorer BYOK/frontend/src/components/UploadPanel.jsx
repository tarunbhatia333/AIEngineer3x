import { useRef, useState } from "react";

export default function UploadPanel({
  collections,
  activeCollection,
  onActivate,
  onDelete,
  onUpload,
  onReingestDefault,
  ingesting,
  ingestStatus,
  disabled,
}) {
  const fileRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = (file) => {
    if (!file || disabled) return;
    onUpload(file);
  };

  return (
    <div className="panel">
      <h2>Knowledge Base</h2>

      <div
        className={"dropzone" + (dragOver ? " dropzone--over" : "") + (disabled ? " dropzone--disabled" : "")}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFile(e.dataTransfer.files?.[0]);
        }}
        onClick={() => !disabled && fileRef.current?.click()}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt,.md"
          hidden
          disabled={disabled}
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <p>Drop a PDF / .txt / .md here, or click to upload</p>
        <span className="dropzone-hint">Ingests into its own namespace</span>
      </div>

      {ingesting && <div className="status status--busy">{ingestStatus}</div>}
      {!ingesting && ingestStatus && <div className="status">{ingestStatus}</div>}

      <div className="collections-list">
        {collections.length === 0 && <p className="muted">No collections yet.</p>}
        {collections.map((c) => (
          <div key={c.name} className={"collection-row" + (c.name === activeCollection ? " collection-row--active" : "")}>
            <div className="collection-info">
              <span className="collection-label">{c.label}</span>
              <span className="collection-meta">{c.chunk_count} chunks</span>
            </div>
            <div className="collection-actions">
              {c.name !== activeCollection && (
                <button className="btn-small" onClick={() => onActivate(c.name)}>
                  Use
                </button>
              )}
              {c.name === activeCollection && <span className="badge">Active</span>}
              {c.name !== "default" && (
                <button className="btn-small btn-danger" onClick={() => onDelete(c.name)}>
                  ✕
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <button className="btn-secondary" onClick={onReingestDefault} disabled={ingesting || disabled}>
        Re-ingest default PDF
      </button>
    </div>
  );
}
