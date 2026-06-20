const BASE = '/api';

async function post(path, body) {
  const r = await fetch(`${BASE}/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || `${path} failed`);
  return data;
}

export async function getConfigStatus() {
  const r = await fetch(`${BASE}/config`);
  if (!r.ok) throw new Error('Failed to load config');
  return r.json();
}

export async function generatePlan(jiraId, config) {
  return post('generate', { jiraId, config });
}

export async function generateTestCases(jiraId, config, sampleSchema, options) {
  return post('generate-test-cases', { jiraId, config, sampleSchema, options });
}

export async function generateTestScripts(testCases, config, options) {
  return post('generate-test-scripts', { testCases, config, options });
}

export async function saveFiles(files) {
  return post('save', { files });
}

export async function savePlan(jiraId, markdown) {
  const r = await saveFiles([{ filename: `test-plan-${jiraId || 'plan'}.md`, content: markdown }]);
  return { path: r.path };
}
