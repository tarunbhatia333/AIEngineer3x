// Layer 3 Tool — multi-provider chat completion. Atomic.
// Dispatches on config.llm.active to the matching provider, each with its own
// endpoint/auth/response shape. All providers expose the same chat(config, messages, opts) contract.

const DEFAULT_MODELS = {
  groq: 'openai/gpt-oss-120b',
  openai: 'gpt-4o-mini',
  anthropic: 'claude-sonnet-4-6',
  azureOpenai: '',
};

function providerConfig(config, provider) {
  return (config.llm && config.llm[provider]) || {};
}

async function groqChat(config, messages, { json, temperature, maxTokens }) {
  const p = providerConfig(config, 'groq');
  if (!p.key) throw new Error('Missing GROQ API key');
  const body = { model: p.model || DEFAULT_MODELS.groq, messages, temperature, max_tokens: maxTokens };
  if (json) body.response_format = { type: 'json_object' };

  const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${p.key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`GROQ ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const data = await res.json();
  return data.choices?.[0]?.message?.content || '';
}

async function openaiChat(config, messages, { json, temperature, maxTokens }) {
  const p = providerConfig(config, 'openai');
  if (!p.key) throw new Error('Missing OpenAI API key');
  const body = { model: p.model || DEFAULT_MODELS.openai, messages, temperature, max_tokens: maxTokens };
  if (json) body.response_format = { type: 'json_object' };

  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${p.key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`OpenAI ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const data = await res.json();
  return data.choices?.[0]?.message?.content || '';
}

async function azureOpenaiChat(config, messages, { json, temperature, maxTokens }) {
  const p = providerConfig(config, 'azureOpenai');
  if (!p.key) throw new Error('Missing Azure OpenAI API key');
  if (!p.endpoint || !p.deployment) throw new Error('Missing Azure OpenAI endpoint or deployment');
  const body = { messages, temperature, max_tokens: maxTokens };
  if (json) body.response_format = { type: 'json_object' };

  const base = p.endpoint.trim().replace(/\/+$/, '');
  const url = `${base}/openai/deployments/${encodeURIComponent(p.deployment)}/chat/completions?api-version=2024-06-01`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'api-key': p.key, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Azure OpenAI ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const data = await res.json();
  return data.choices?.[0]?.message?.content || '';
}

// Anthropic's Messages API takes `system` separately and has no JSON response_format,
// so JSON mode here relies on the prompt's "return ONLY JSON" instruction.
async function anthropicChat(config, messages, { temperature, maxTokens }) {
  const p = providerConfig(config, 'anthropic');
  if (!p.key) throw new Error('Missing Anthropic API key');

  const system = messages.filter((m) => m.role === 'system').map((m) => m.content).join('\n\n');
  const rest = messages.filter((m) => m.role !== 'system');

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': p.key,
      'anthropic-version': '2023-06-01',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: p.model || DEFAULT_MODELS.anthropic,
      max_tokens: maxTokens,
      temperature,
      system: system || undefined,
      messages: rest,
    }),
  });
  if (!res.ok) throw new Error(`Anthropic ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const data = await res.json();
  return (data.content || []).map((b) => b.text || '').join('');
}

const PROVIDERS = { groq: groqChat, openai: openaiChat, anthropic: anthropicChat, azureOpenai: azureOpenaiChat };

export async function chat(config, messages, { json = true, temperature = 0.3, maxTokens = 8000 } = {}) {
  const active = config.llm?.active || 'groq';
  const fn = PROVIDERS[active];
  if (!fn) throw new Error(`Unknown LLM provider: ${active}`);

  const finalMessages = json
    ? messages.map((m, i) =>
        i === 0 && m.role === 'system'
          ? { ...m, content: `${m.content} Output strictly valid JSON and nothing else.` }
          : m,
      )
    : messages;

  const content = await fn(config, finalMessages, { json, temperature, maxTokens });
  if (!json) return content;

  try {
    const cleaned = content.trim().replace(/^```(?:json)?\n?/i, '').replace(/```$/, '');
    return JSON.parse(cleaned);
  } catch {
    throw new Error(`${active} did not return valid JSON`);
  }
}
