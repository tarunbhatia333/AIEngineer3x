import React, { useState } from 'react';

function toMarkdownTable(columns, rows) {
  const head = `| ${columns.join(' | ')} |`;
  const sep = `| ${columns.map(() => '---').join(' | ')} |`;
  const body = rows.map((r) => `| ${columns.map((c) => String(r[c] ?? 'TBD').replace(/\n/g, '<br>')).join(' | ')} |`);
  return [head, sep, ...body].join('\n');
}

export default function TestCasesView({ columns, testCases, onChange }) {
  const [raw, setRaw] = useState(false);

  function updateCell(rowIdx, col, value) {
    const next = testCases.map((r, i) => (i === rowIdx ? { ...r, [col]: value } : r));
    onChange(next);
  }

  return (
    <div className="plan">
      <div className="plan-head">
        <div>
          <h3>{testCases.length} test case(s)</h3>
          <p className="meta">Columns: {columns.join(', ')}</p>
        </div>
        <button className="ghost" onClick={() => setRaw((r) => !r)}>
          {raw ? 'Table' : 'Markdown'}
        </button>
      </div>

      {raw ? (
        <pre className="md">{toMarkdownTable(columns, testCases)}</pre>
      ) : (
        <div className="table-wrap">
          <table className="editable">
            <thead>
              <tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr>
            </thead>
            <tbody>
              {testCases.map((row, i) => (
                <tr key={i}>
                  {columns.map((c) => (
                    <td key={c}>
                      <textarea
                        value={row[c] ?? ''}
                        onChange={(e) => updateCell(i, c, e.target.value)}
                        rows={1}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
