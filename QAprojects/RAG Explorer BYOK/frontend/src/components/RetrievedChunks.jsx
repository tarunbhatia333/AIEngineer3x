export default function RetrievedChunks({ chunks }) {
  if (!chunks || chunks.length === 0) return null;
  return (
    <div className="chunks">
      <h3>Retrieved Chunks ({chunks.length})</h3>
      <div className="chunks-grid">
        {chunks.map((c, i) => (
          <div key={i} className="chunk-card">
            <div className="chunk-card-header">
              <span className="chunk-index">#{i + 1}</span>
              <span className="chunk-score">score {c.score}</span>
            </div>
            <p className="chunk-text">{c.text}</p>
            <div className="chunk-source">
              {c.source} · page {c.page}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
