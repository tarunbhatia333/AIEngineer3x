// Vercel serverless function: POST /api/generate-test-scripts — test cases -> LLM -> Selenium Python files.
import { generateTestScripts } from '../tools/testScripts.js';
import { mergeConfig } from '../tools/mergeConfig.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : req.body || {};
    const testCases = body.testCases;
    if (!testCases || (Array.isArray(testCases) && !testCases.length)) {
      return res.status(400).json({ error: 'Missing testCases' });
    }

    const config = mergeConfig(body);
    const { files, errors } = await generateTestScripts(config, testCases, body.options);

    res.status(200).json({ files, errors });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
