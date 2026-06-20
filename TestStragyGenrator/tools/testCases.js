// Layer 3 Tool — build the prompt, generate test cases via the active LLM.
// Boundary rule (BLAST): the LLM produces CONTENT (JSON); table/CSV rendering is deterministic code.
import { chat } from './llmClient.js';

const DEFAULT_COLUMNS = ['id', 'title', 'preconditions', 'steps', 'expectedResult', 'priority'];

function columnsFromSchema(sampleSchema) {
  if (sampleSchema?.headers?.length) return sampleSchema.headers;
  return DEFAULT_COLUMNS;
}

export function buildMessages(issue, sampleSchema, options = {}) {
  const columns = columnsFromSchema(sampleSchema);
  const { count = 8, platform = 'Web', notes = '' } = options;

  const system = [
    'You are a senior QA engineer writing detailed, executable test cases.',
    'Base everything strictly on the provided ticket. If information is missing, use "TBD" — never invent specific facts.',
    'Be concrete, professional, and concise.',
  ].join(' ');

  const lines = [
    `Generate exactly ${count} test cases for the following ticket.`,
    `Target platform: ${platform}.`,
    notes ? `Additional notes: ${notes}` : '',
    '',
    `Key: ${issue.key}`,
    `Summary: ${issue.summary}`,
    `Type: ${issue.issueType} | Status: ${issue.status} | Priority: ${issue.priority}`,
    '',
    'Description / Acceptance Criteria:',
    issue.description || '(none provided)',
    '',
  ];

  if (sampleSchema?.headers?.length) {
    lines.push(
      'A sample file was uploaded as a FORMAT REFERENCE. Match its column structure exactly — use these',
      `exact keys for every test case object: ${JSON.stringify(columns)}.`,
      sampleSchema.sampleRows?.length
        ? `Sample rows for reference (do not repeat them verbatim): ${JSON.stringify(sampleSchema.sampleRows)}`
        : '',
      '',
    );
  } else {
    lines.push(`Use these exact keys for every test case object: ${JSON.stringify(columns)}.`, '');
  }

  lines.push(
    'Return ONLY a JSON object: { "testCases": [ { <one entry per key above, all string values; if a',
    'column represents steps, return it as a single newline-separated string> } ] }',
  );

  return [
    { role: 'system', content: system },
    { role: 'user', content: lines.filter(Boolean).join('\n') },
  ];
}

export async function generateTestCases(config, issue, sampleSchema, options) {
  const result = await chat(config, buildMessages(issue, sampleSchema, options), { json: true, temperature: 0.4 });
  const testCases = Array.isArray(result.testCases) ? result.testCases : [];
  return { columns: columnsFromSchema(sampleSchema), testCases };
}
