import React, { useState } from 'react';

const PROVIDER_FIELDS = {
  groq: [{ key: 'key', label: 'GROQ API Key', placeholder: 'gsk_...' }, { key: 'model', label: 'Model', placeholder: 'openai/gpt-oss-120b' }],
  openai: [{ key: 'key', label: 'OpenAI API Key', placeholder: 'sk-...' }, { key: 'model', label: 'Model', placeholder: 'gpt-4o-mini' }],
  anthropic: [{ key: 'key', label: 'Anthropic API Key', placeholder: 'sk-ant-...' }, { key: 'model', label: 'Model', placeholder: 'claude-sonnet-4-6' }],
  azureOpenai: [
    { key: 'key', label: 'Azure OpenAI API Key', placeholder: '...' },
    { key: 'endpoint', label: 'Endpoint', placeholder: 'https://your-resource.openai.azure.com' },
    { key: 'deployment', label: 'Deployment name', placeholder: 'gpt-4o-mini' },
  ],
};

const PROVIDER_LABELS = { groq: 'GROQ', openai: 'OpenAI', anthropic: 'Anthropic', azureOpenai: 'Azure OpenAI' };

export default function Settings({ config, onSave, envStatus }) {
  const [form, setForm] = useState(config);
  const [activeTab, setActiveTab] = useState(config.llm?.active || 'groq');
  const [saved, setSaved] = useState(false);

  function update(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
    setSaved(false);
  }

  function updateLlmField(provider, field, value) {
    setForm((f) => ({
      ...f,
      llm: { ...f.llm, [provider]: { ...f.llm?.[provider], [field]: value } },
    }));
    setSaved(false);
  }

  function updateAzureField(field, value) {
    setForm((f) => ({ ...f, azure: { ...f.azure, [field]: value } }));
    setSaved(false);
  }

  function submit(e) {
    e.preventDefault();
    onSave({ ...form, llm: { ...form.llm, active: activeTab } });
    setSaved(true);
  }

  return (
    <section className="card">
      <h2>Settings</h2>
      <p className="muted">
        Stored locally in your browser. Blank fields fall back to the server <code>.env</code>. Keys are
        never logged.
      </p>

      <form onSubmit={submit} className="form">
        <h3>Data Source</h3>
        <div className="source-pills">
          <button type="button" className={form.dataSource !== 'azure' ? 'active' : ''} onClick={() => update('dataSource', 'jira')}>
            Jira
          </button>
          <button type="button" className={form.dataSource === 'azure' ? 'active' : ''} onClick={() => update('dataSource', 'azure')}>
            Azure DevOps
          </button>
        </div>

        {form.dataSource !== 'azure' ? (
          <>
            <label className="field">
              <span>Jira Base URL</span>
              <input value={form.jiraUrl || ''} placeholder="https://your-domain.atlassian.net" onChange={(e) => update('jiraUrl', e.target.value)} autoComplete="off" spellCheck="false" />
            </label>
            <label className="field">
              <span>Jira Email</span>
              <input value={form.jiraEmail || ''} placeholder="you@example.com" onChange={(e) => update('jiraEmail', e.target.value)} autoComplete="off" spellCheck="false" />
            </label>
            <label className="field">
              <span>Jira API Token</span>
              <input type="password" value={form.jiraToken || ''} placeholder="ATATT..." onChange={(e) => update('jiraToken', e.target.value)} autoComplete="off" spellCheck="false" />
            </label>
          </>
        ) : (
          <>
            <label className="field">
              <span>Organization URL</span>
              <input value={form.azure?.orgUrl || ''} placeholder="https://dev.azure.com/your-org" onChange={(e) => updateAzureField('orgUrl', e.target.value)} autoComplete="off" spellCheck="false" />
            </label>
            <label className="field">
              <span>Project</span>
              <input value={form.azure?.project || ''} placeholder="MyProject" onChange={(e) => updateAzureField('project', e.target.value)} autoComplete="off" spellCheck="false" />
            </label>
            <label className="field">
              <span>Personal Access Token (PAT)</span>
              <input type="password" value={form.azure?.pat || ''} placeholder="..." onChange={(e) => updateAzureField('pat', e.target.value)} autoComplete="off" spellCheck="false" />
            </label>
          </>
        )}

        <h3>LLM Providers</h3>
        <div className="tabs provider-tabs">
          {Object.keys(PROVIDER_LABELS).map((p) => (
            <button key={p} type="button" className={activeTab === p ? 'active' : ''} onClick={() => setActiveTab(p)}>
              {PROVIDER_LABELS[p]}
              {envStatus?.providers?.[p] && ' ✓'}
            </button>
          ))}
        </div>
        <p className="muted">Active provider used for generation: <strong>{PROVIDER_LABELS[activeTab]}</strong></p>

        {PROVIDER_FIELDS[activeTab].map((f) => (
          <label key={f.key} className="field">
            <span>{f.label}</span>
            <input
              type={f.key === 'key' ? 'password' : 'text'}
              value={form.llm?.[activeTab]?.[f.key] || ''}
              placeholder={f.placeholder}
              onChange={(e) => updateLlmField(activeTab, f.key, e.target.value)}
              autoComplete="off"
              spellCheck="false"
            />
          </label>
        ))}

        <div className="row">
          <button type="submit" className="primary">Save settings</button>
          {saved && <span className="ok">Saved ✓</span>}
        </div>
      </form>

      {envStatus && (
        <div className="envbox">
          <h3>Server <code>.env</code> status</h3>
          <ul>
            <li>Jira URL: {envStatus.jiraUrl ? <code>{envStatus.jiraUrl}</code> : <em>not set</em>}</li>
            <li>Jira Email: {envStatus.jiraEmail ? <code>{envStatus.jiraEmail}</code> : <em>not set</em>}</li>
            <li>Jira Token: {envStatus.hasJiraToken ? 'set ✓' : <em>not set</em>}</li>
            <li>Azure DevOps: {envStatus.hasAzureDevOps ? 'set ✓' : <em>not set</em>}</li>
            <li>Default active provider: <code>{envStatus.activeProvider}</code></li>
            {Object.keys(PROVIDER_LABELS).map((p) => (
              <li key={p}>
                {PROVIDER_LABELS[p]} key: {envStatus.providers?.[p] ? 'set ✓' : <em>not set</em>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
