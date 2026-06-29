import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { downloadBlob, buildZip } from '../lib/files.js';

function languageFor(filename) {
  return filename.endsWith('.java') ? 'java' : 'python';
}

export default function TestScriptsView({ files }) {
  const [openIdx, setOpenIdx] = useState(0);

  async function downloadAll() {
    if (files.length === 1) {
      downloadBlob(new Blob([files[0].content], { type: 'text/plain' }), files[0].filename);
      return;
    }
    const zip = await buildZip(files);
    downloadBlob(zip, 'test-scripts.zip');
  }

  return (
    <div className="plan">
      <div className="plan-head">
        <h3>{files.length} script file(s)</h3>
        <button className="ghost" onClick={downloadAll}>
          ⬇ {files.length > 1 ? 'Download all (.zip)' : `Download ${files[0]?.filename || ''}`}
        </button>
      </div>

      <div className="code-files">
        {files.map((f, i) => (
          <div key={f.filename} className="code-file">
            <button type="button" className="code-file-head" onClick={() => setOpenIdx(openIdx === i ? -1 : i)}>
              <span>📄 {f.filename}</span>
              <span>{openIdx === i ? '▾' : '▸'}</span>
            </button>
            {openIdx === i && (
              <SyntaxHighlighter language={languageFor(f.filename)} style={oneDark} customStyle={{ margin: 0, borderRadius: '0 0 10px 10px' }}>
                {f.content}
              </SyntaxHighlighter>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
