import React, { useEffect, useState } from 'react';
import Settings from './components/Settings.jsx';
import Generator from './components/Generator.jsx';
import ModePicker from './components/ModePicker.jsx';
import TestCasesGenerator from './components/TestCasesGenerator.jsx';
import TestScriptsGenerator from './components/TestScriptsGenerator.jsx';
import { getConfigStatus } from './lib/api.js';

const STORAGE_KEY = 'blast.config.v2';
const THEME_KEY = 'blast.theme';
const emptyConfig = {
  jiraUrl: '',
  jiraEmail: '',
  jiraToken: '',
  dataSource: 'jira',
  azure: { orgUrl: '', project: '', pat: '' },
  llm: {
    active: 'groq',
    groq: { key: '', model: '' },
    openai: { key: '', model: '' },
    anthropic: { key: '', model: '' },
    azureOpenai: { key: '', endpoint: '', deployment: '' },
  },
};

export default function App() {
  const [tab, setTab] = useState('generate');
  const [mode, setMode] = useState('picker'); // picker | plan | cases | scripts
  const [jiraId, setJiraId] = useState('VWO-48');
  const [testCaseHistory, setTestCaseHistory] = useState([]); // last 2 generations, newest first
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || 'dark');
  const [config, setConfig] = useState(() => {
    try {
      return { ...emptyConfig, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') };
    } catch {
      return emptyConfig;
    }
  });
  const [envStatus, setEnvStatus] = useState(null);

  useEffect(() => {
    getConfigStatus().then(setEnvStatus).catch(() => setEnvStatus(null));
  }, []);

  useEffect(() => {
    document.body.classList.toggle('light', theme === 'light');
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  function saveConfig(next) {
    setConfig(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }

  function goSettings() {
    setTab('settings');
  }

  function recordTestCases(ticketId, columns, testCases) {
    setTestCaseHistory((h) => [
      { id: Date.now(), ticketId, columns, testCases, generatedAt: new Date().toISOString() },
      ...h,
    ].slice(0, 2));
  }

  function goToScripts() {
    setMode('scripts');
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">🚀</span>
          <div>
            <h1>E2E TestCase Generator</h1>
            <p className="sub">Test Plan · Test Cases · Test Scripts</p>
          </div>
        </div>
        <div className="topbar-right">
          <nav className="tabs">
            <button className={tab === 'generate' ? 'active' : ''} onClick={() => setTab('generate')}>Generate</button>
            <button className={tab === 'settings' ? 'active' : ''} onClick={() => setTab('settings')}>Settings</button>
          </nav>
          <button className="theme-toggle" onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}>
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </header>

      <main className="content">
        {tab === 'settings' ? (
          <Settings config={config} onSave={saveConfig} envStatus={envStatus} />
        ) : mode === 'picker' ? (
          <ModePicker onSelect={setMode} />
        ) : mode === 'plan' ? (
          <Generator
            config={config}
            envStatus={envStatus}
            goSettings={goSettings}
            goPicker={() => setMode('picker')}
            dataSource={config.dataSource}
            onDataSourceChange={(ds) => saveConfig({ ...config, dataSource: ds })}
            jiraId={jiraId}
            onJiraIdChange={setJiraId}
          />
        ) : mode === 'cases' ? (
          <TestCasesGenerator
            config={config}
            envStatus={envStatus}
            goSettings={goSettings}
            goPicker={() => setMode('picker')}
            dataSource={config.dataSource}
            onDataSourceChange={(ds) => saveConfig({ ...config, dataSource: ds })}
            ticketId={jiraId}
            onTicketIdChange={setJiraId}
            onGenerated={recordTestCases}
            onUseForScripts={goToScripts}
          />
        ) : (
          <TestScriptsGenerator
            config={config}
            envStatus={envStatus}
            goSettings={goSettings}
            goPicker={() => setMode('picker')}
            testCaseHistory={testCaseHistory}
          />
        )}
      </main>

      <footer className="foot">Lightweight React · Express proxy · credentials stay local</footer>
    </div>
  );
}
