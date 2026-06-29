import React from 'react';

const MODES = [
  {
    id: 'test-plan',
    title: 'Test Plan',
    description: 'Generate a structured test plan from a Jira ticket',
    icon: '📋'
  },
  {
    id: 'test-cases',
    title: 'Test Cases',
    description: 'Generate detailed test cases from Jira data, an uploaded file, or custom input',
    icon: '✅'
  },
  {
    id: 'test-scripts',
    title: 'Test Scripts',
    description: 'Generate Selenium (Python) automation scripts from test cases',
    icon: '🤖'
  }
];

export default function ModeSelector({ onSelect }) {
  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>What would you like to generate?</h3>
        <p className="muted">Select a generation mode to continue</p>
        <div className="mode-grid">
          {MODES.map((mode) => (
            <button
              key={mode.id}
              className="mode-card"
              onClick={() => onSelect(mode.id)}
            >
              <div className="mode-icon">{mode.icon}</div>
              <h4>{mode.title}</h4>
              <p>{mode.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
