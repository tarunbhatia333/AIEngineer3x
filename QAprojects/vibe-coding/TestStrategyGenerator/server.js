// Layer 2 — Navigation. Express proxy: routes request -> ticketSource -> generator(llmClient) -> response.
// Also fixes browser CORS to Jira/Azure DevOps and keeps API tokens server-side.
import express from 'express';
import dotenv from 'dotenv';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { fetchTicket } from './tools/ticketSource.js';
import { generateTestPlan, renderMarkdown } from './tools/testPlan.js';
import { generateTestCases } from './tools/testCases.js';
import { generateTestScripts } from './tools/testScripts.js';
import { mergeConfig, configStatus } from './tools/mergeConfig.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, '.env') });

const PORT = process.env.PORT || 8787;
const app = express();
app.use(express.json({ limit: '5mb' }));

// Non-secret config presence, so the UI can prefill + warn.
app.get('/api/config', (_req, res) => {
  res.json(configStatus());
});

app.post('/api/generate', async (req, res) => {
  try {
    const jiraId = (req.body?.jiraId || '').trim();
    if (!jiraId) return res.status(400).json({ error: 'Missing jiraId' });

    const config = mergeConfig(req.body);
    const issue = await fetchTicket(config, jiraId);
    const plan = await generateTestPlan(config, issue);
    const markdown = renderMarkdown(plan, issue, config);

    res.json({ issue, plan, markdown });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/generate-test-cases', async (req, res) => {
  try {
    const jiraId = (req.body?.jiraId || '').trim();
    if (!jiraId) return res.status(400).json({ error: 'Missing jiraId' });

    const config = mergeConfig(req.body);
    const issue = await fetchTicket(config, jiraId);
    const { columns, testCases } = await generateTestCases(config, issue, req.body?.sampleSchema, req.body?.options);

    res.json({ issue, columns, testCases });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/generate-test-scripts', async (req, res) => {
  try {
    const testCases = req.body?.testCases;
    if (!testCases || (Array.isArray(testCases) && !testCases.length)) {
      return res.status(400).json({ error: 'Missing testCases' });
    }

    const config = mergeConfig(req.body);
    const { files, errors } = await generateTestScripts(config, testCases, req.body?.options);

    res.json({ files, errors });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/save', (req, res) => {
  try {
    const files = Array.isArray(req.body?.files) ? req.body.files : [];
    if (!files.length) return res.status(400).json({ error: 'Missing files' });

    const dir = path.join(__dirname, 'output');
    fs.mkdirSync(dir, { recursive: true });

    const paths = files.map(({ filename, content, encoding }) => {
      const safeName = (filename || 'file.txt').replace(/[^A-Za-z0-9_.-]/g, '_');
      fs.writeFileSync(path.join(dir, safeName), content, encoding === 'base64' ? 'base64' : 'utf8');
      return `output/${safeName}`;
    });

    res.json({ paths, path: paths[0] });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Serve the built frontend in production (after `npm run build`).
const dist = path.join(__dirname, 'dist');
if (fs.existsSync(dist)) {
  app.use(express.static(dist));
  app.get(/^(?!\/api).*/, (_req, res) => res.sendFile(path.join(dist, 'index.html')));
}

app.listen(PORT, () => console.log(`[server] proxy listening on http://localhost:${PORT}`));
