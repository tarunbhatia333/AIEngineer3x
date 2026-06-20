// Layer 3 Tool — build the prompt, generate Selenium automation scripts via the active LLM.
// Source code is returned as plain text with delimiters, NOT as a JSON string value — asking an LLM
// to embed full source (quotes, backslashes, newlines) inside a JSON string is exactly the kind of
// thing that trips strict JSON-mode validators (seen failing on GROQ for Java/TestNG output).
import { chat } from './llmClient.js';

// framework -> { language, ext, conventions } so the prompt and output match the chosen stack.
const FRAMEWORKS = {
  pytest: { language: 'Python', ext: 'py', conventions: 'pytest (fixtures, plain assert statements, snake_case test_ functions)' },
  unittest: { language: 'Python', ext: 'py', conventions: 'unittest (unittest.TestCase subclasses, setUp/tearDown, self.assert* methods)' },
  testng: { language: 'Java', ext: 'java', conventions: 'TestNG (@Test, @BeforeMethod/@AfterMethod annotations, Assert.assert* from org.testng.Assert, one public class per file matching the filename)' },
};

const FILE_BLOCK_RE = /===FILE:\s*(.+?)\s*===\r?\n([\s\S]*?)\r?\n===END===/g;

function formatTestCases(testCases) {
  if (typeof testCases === 'string') return testCases;
  if (!Array.isArray(testCases) || !testCases.length) return '(none provided)';
  return testCases
    .map((tc, i) => {
      const entries = Object.entries(tc).map(([k, v]) => `  ${k}: ${v}`).join('\n');
      return `Test Case ${i + 1}:\n${entries}`;
    })
    .join('\n\n');
}

// `multiFile` controls the wording only — buildMessages always describes the test cases it's given,
// whether that's the full batch (oneFile mode) or a single test case (one request per file, below).
export function buildMessages(testCases, options = {}, multiFile = !options.oneFile) {
  const { browser = 'Chrome', framework = 'pytest', pageObjectModel = false, baseUrl = '' } = options;
  const fw = FRAMEWORKS[framework] || FRAMEWORKS.pytest;

  const system = [
    `You are a senior SDET writing Selenium WebDriver automation in ${fw.language}.`,
    'Produce working, idiomatic, well-structured code. Use explicit waits, never sleep-based synchronization.',
    'If information is missing, use a clearly marked TODO comment — never invent specific selectors or URLs.',
  ].join(' ');

  const lines = [
    `Framework: ${framework} — use ${fw.conventions}.`,
    `Target browser: ${browser}.`,
    `Page Object Model: ${pageObjectModel ? 'yes — separate page object classes from test logic' : 'no — keep tests flat'}.`,
    baseUrl ? `Base URL / environment: ${baseUrl}.` : 'No base URL given — use a TODO placeholder.',
    multiFile
      ? `Produce ONE ${fw.language} file PER test case below.`
      : `Produce exactly ONE ${fw.language} file covering the test case(s) below.`,
    '',
    'Test cases:',
    formatTestCases(testCases),
    '',
    'Output format — plain text, NOT JSON, NOT markdown code fences. For each file, output exactly:',
    '===FILE: filename.ext===',
    '<full source code for that file, nothing else on these lines>',
    '===END===',
    multiFile ? 'Output one ===FILE===...===END=== block per test case, in order.' : 'Output exactly one ===FILE===...===END=== block.',
    `Each filename must end in .${fw.ext}.`,
  ];

  return [
    { role: 'system', content: system },
    { role: 'user', content: lines.filter(Boolean).join('\n') },
  ];
}

function parseFileBlocks(text) {
  const files = [];
  let match;
  FILE_BLOCK_RE.lastIndex = 0;
  while ((match = FILE_BLOCK_RE.exec(text))) {
    files.push({ filename: match[1].trim(), content: match[2].trim() });
  }
  return files;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Rate-limit errors (GROQ/OpenAI 429) name an exact retry delay ("try again in 7.74s") — honor it
// instead of guessing, so per-test-case generation eventually finishes on tight free-tier budgets.
function retryDelayMs(message) {
  const match = /try again in ([\d.]+)\s*s/i.exec(message || '');
  return match ? Math.ceil(parseFloat(match[1]) * 1000) + 500 : null;
}

async function chatWithRetry(config, messages, opts, maxAttempts = 4) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await chat(config, messages, opts);
    } catch (err) {
      const isRateLimit = /429|rate limit/i.test(err.message);
      const delay = isRateLimit ? retryDelayMs(err.message) : null;
      if (!delay || attempt === maxAttempts) throw err;
      await sleep(delay);
    }
  }
}

// Many small requests (one per test case) instead of one giant request — this keeps each call well
// under per-minute token limits (free-tier GROQ caps at 8000 TPM) and means a single LLM hiccup
// can't truncate the whole batch: each file either succeeds or fails independently.
export async function generateTestScripts(config, testCases, options = {}) {
  if (options.oneFile || typeof testCases === 'string' || !Array.isArray(testCases) || testCases.length <= 1) {
    const text = await chatWithRetry(config, buildMessages(testCases, options, false), { json: false, temperature: 0.3, maxTokens: 5000 });
    const files = parseFileBlocks(text);
    if (!files.length) throw new Error('The LLM did not return any recognizable script files');
    return { files };
  }

  const files = [];
  const errors = [];
  for (let i = 0; i < testCases.length; i++) {
    if (i > 0) await sleep(1200); // spread sequential calls across the per-minute token budget
    try {
      const text = await chatWithRetry(config, buildMessages([testCases[i]], options, true), { json: false, temperature: 0.3, maxTokens: 3000 });
      const found = parseFileBlocks(text);
      if (!found.length) throw new Error('no recognizable file block returned');
      files.push(...found);
    } catch (err) {
      errors.push(`Test case ${i + 1}: ${err.message}`);
    }
  }

  if (!files.length) throw new Error(`Failed to generate any scripts: ${errors.join('; ')}`);
  return { files, errors: errors.length ? errors : undefined };
}
