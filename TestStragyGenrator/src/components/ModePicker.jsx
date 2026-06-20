import React from 'react';

const MODES = [
  { key: 'plan', title: 'Test Plan', desc: 'Generate a structured test plan from a Jira ticket' },
  { key: 'cases', title: 'Test Cases', desc: 'Generate detailed test cases from Jira data, an uploaded file, or custom input' },
  { key: 'scripts', title: 'Test Scripts', desc: 'Generate Selenium (Python) automation scripts from test cases' },
];

export default function ModePicker({ onSelect }) {
  return (
    <section className="card">
      <h2>What would you like to generate?</h2>
      <p className="muted">Pick a mode to get started.</p>
      <div className="mode-grid">
        {MODES.map((m) => (
          <button key={m.key} className="mode-card" onClick={() => onSelect(m.key)}>
            <h3>{m.title}</h3>
            <p>{m.desc}</p>
          </button>
        ))}
      </div>
    </section>
  );
}
