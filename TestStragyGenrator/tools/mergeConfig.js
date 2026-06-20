// Layer 2 helper — merges UI-provided config with server .env defaults.
// UI-provided non-empty values win; blank fields fall back to .env.

function pick(uiVal, envVal) {
  return (uiVal || '').toString().trim() || envVal || '';
}

export function envDefaults() {
  return {
    jiraUrl: process.env.JIRA_URL || '',
    jiraEmail: process.env.JIRA_EMAIL || '',
    jiraToken: process.env.JIRA_API_TOKEN || process.env.JIRA_TOKEN || '',
    azure: {
      orgUrl: process.env.AZURE_DEVOPS_ORG_URL || '',
      project: process.env.AZURE_DEVOPS_PROJECT || '',
      pat: process.env.AZURE_DEVOPS_PAT || '',
    },
    llm: {
      active: process.env.LLM_PROVIDER || 'groq',
      groq: { key: process.env.GROQ_KEY || '', model: process.env.GROQ_MODEL || '' },
      openai: { key: process.env.OPENAI_KEY || '', model: process.env.OPENAI_MODEL || '' },
      anthropic: { key: process.env.ANTHROPIC_KEY || '', model: process.env.ANTHROPIC_MODEL || '' },
      azureOpenai: {
        key: process.env.AZURE_OPENAI_KEY || '',
        endpoint: process.env.AZURE_OPENAI_ENDPOINT || '',
        deployment: process.env.AZURE_OPENAI_DEPLOYMENT || '',
      },
    },
  };
}

export function mergeConfig(body = {}) {
  const env = envDefaults();
  const c = body.config || {};
  const llm = c.llm || {};
  const azure = c.azure || {};

  return {
    jiraUrl: pick(c.jiraUrl, env.jiraUrl),
    jiraEmail: pick(c.jiraEmail, env.jiraEmail),
    jiraToken: pick(c.jiraToken, env.jiraToken),
    dataSource: c.dataSource === 'azure' ? 'azure' : 'jira',
    azure: {
      orgUrl: pick(azure.orgUrl, env.azure.orgUrl),
      project: pick(azure.project, env.azure.project),
      pat: pick(azure.pat, env.azure.pat),
    },
    llm: {
      active: llm.active || env.llm.active,
      groq: { key: pick(llm.groq?.key, env.llm.groq.key), model: pick(llm.groq?.model, env.llm.groq.model) },
      openai: { key: pick(llm.openai?.key, env.llm.openai.key), model: pick(llm.openai?.model, env.llm.openai.model) },
      anthropic: {
        key: pick(llm.anthropic?.key, env.llm.anthropic.key),
        model: pick(llm.anthropic?.model, env.llm.anthropic.model),
      },
      azureOpenai: {
        key: pick(llm.azureOpenai?.key, env.llm.azureOpenai.key),
        endpoint: pick(llm.azureOpenai?.endpoint, env.llm.azureOpenai.endpoint),
        deployment: pick(llm.azureOpenai?.deployment, env.llm.azureOpenai.deployment),
      },
    },
  };
}

export function configStatus() {
  const env = envDefaults();
  return {
    jiraUrl: env.jiraUrl,
    jiraEmail: env.jiraEmail,
    hasJiraToken: Boolean(env.jiraToken),
    dataSource: 'jira',
    hasAzureDevOps: Boolean(env.azure.orgUrl && env.azure.project && env.azure.pat),
    activeProvider: env.llm.active,
    providers: {
      groq: Boolean(env.llm.groq.key),
      openai: Boolean(env.llm.openai.key),
      anthropic: Boolean(env.llm.anthropic.key),
      azureOpenai: Boolean(env.llm.azureOpenai.key && env.llm.azureOpenai.endpoint && env.llm.azureOpenai.deployment),
    },
  };
}
