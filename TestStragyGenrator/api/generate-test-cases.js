// Vercel serverless function: POST /api/generate-test-cases — ticket fetch -> LLM -> structured test cases.
import { fetchTicket } from '../tools/ticketSource.js';
import { generateTestCases } from '../tools/testCases.js';
import { mergeConfig } from '../tools/mergeConfig.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : req.body || {};
    const jiraId = (body.jiraId || '').trim();
    if (!jiraId) return res.status(400).json({ error: 'Missing jiraId' });

    const config = mergeConfig(body);
    const issue = await fetchTicket(config, jiraId);
    const { columns, testCases } = await generateTestCases(config, issue, body.sampleSchema, body.options);

    res.status(200).json({ issue, columns, testCases });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
