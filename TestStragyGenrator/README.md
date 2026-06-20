# E2E TestCase Generator (B.L.A.S.T.)

Lightweight **React + Express** app that turns a Jira or Azure DevOps ticket into one of three QA
artifacts, using whichever LLM provider you configure:

- **Test Plan** — a formal 13-section QA test plan, rendered on screen + downloadable Markdown.
- **Test Cases** — structured test cases (optionally matching the column format of an uploaded
  CSV/XLSX sample), editable in a table, downloadable as CSV/XLSX.
- **Test Scripts** — Selenium automation in **Python (pytest/unittest)** or **Java (TestNG)**,
  generated from test cases you just created, uploaded, or pasted; downloadable as `.py`/`.java` or a
  `.zip`.

Built with the **B.L.A.S.T.** protocol (Blueprint → Link → Architect → Stylize → Trigger) and the
**A.N.T.** 3-layer architecture.

## Architecture
```
React UI (src/)  ──/api──►  Express proxy (server.js)
                              ├─ tools/ticketSource.js     (Jira or Azure DevOps, by config.dataSource)
                              │    ├─ tools/jiraClient.js
                              │    └─ tools/azureDevOpsClient.js
                              ├─ tools/llmClient.js         (GROQ / OpenAI / Anthropic / Azure OpenAI)
                              ├─ tools/testPlan.js          (prompt → JSON → Markdown)
                              ├─ tools/testCases.js         (prompt → structured JSON)
                              └─ tools/testScripts.js       (prompt → delimited source files)
architecture/  = Layer 1 SOPs   ·   tools/ = Layer 3 engines   ·   server.js = Layer 2 routing
```
A proxy is required because Jira/Azure DevOps REST blocks browser CORS; it also keeps API tokens off
the client. The LLM produces **content** (JSON or delimited source text); rendering, table parsing,
and file I/O are deterministic code in `tools/`.

Same logic is duplicated as Vercel serverless functions under `api/` for production deploys
(`api/config.js`, `api/generate.js`, `api/generate-test-cases.js`, `api/generate-test-scripts.js`,
`api/save.js`).

## Setup
1. Copy `.env` and fill in what you need (or enter the same values in the app's **Settings** tab):
   ```
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_EMAIL=you@example.com
   JIRA_API_TOKEN=ATATT...

   LLM_PROVIDER=groq            # groq | openai | anthropic | azureOpenai
   GROQ_KEY=gsk_...
   OPENAI_KEY=                  # optional
   ANTHROPIC_KEY=                # optional
   AZURE_OPENAI_KEY=             # optional, + AZURE_OPENAI_ENDPOINT / _DEPLOYMENT
   AZURE_DEVOPS_ORG_URL=         # optional, + AZURE_DEVOPS_PROJECT / _PAT
   ```
   - Jira API token: https://id.atlassian.com/manage-profile/security/api-tokens
   - GROQ key (free): https://console.groq.com/keys — note the **free tier caps at 8000 tokens/minute**,
     which is why large Test Scripts batches generate one file at a time with automatic retry/backoff.
2. Install: `npm install`

## Run
- **Dev** (Vite + proxy, hot reload):
  ```
  npm run dev
  ```
  Open http://localhost:5173. See `.claude/skills/run-app/SKILL.md` for restart/troubleshooting steps
  and curl-based smoke tests for each endpoint.
- **Verify Jira + GROQ connections only**:
  ```
  npm run handshake          # defaults to VWO-48
  npm run handshake ABC-123
  ```
- **Production** (build then serve from Express):
  ```
  npm run build
  npm start                  # http://localhost:8787
  ```

## Usage
1. **Settings** tab → pick a data source (Jira / Azure DevOps), enter its credentials, and configure
   one or more LLM providers (GROQ / OpenAI / Anthropic / Azure OpenAI) — pick which is active.
2. **Generate** → choose a mode: **Test Plan**, **Test Cases**, or **Test Scripts**.
3. Each mode shares a ticket ID + data-source toggle. Test Cases additionally accepts a sample
   CSV/XLSX (used as a format reference, not appended to) plus count/platform/notes. Test Scripts
   pulls test cases from the last 2 generated batches, an uploaded file, or pasted text, plus
   browser/framework/Page-Object-Model/base-URL options.
4. View results, toggle Markdown/table/code views, **Download**, or **Save to server** (`output/`).

## Deploy (Vercel)
On Vercel the Express proxy becomes **serverless functions** under `api/`; the Vite frontend is served
statically. Config lives in `vercel.json`.

```bash
npx vercel link --yes --project testplanbuddy
npx vercel deploy --prod
```

Set credentials as Project → Settings → Environment Variables in the Vercel dashboard (same keys as
`.env` above) — or enter them in the app's **Settings** tab at runtime.

> Note: "Save to server" is disabled on Vercel (serverless filesystem is read-only) — use the
> Download buttons instead. It still works in local `npm run dev` / `npm start`.

## Notes
- The generator never invents missing data — gaps render as `TBD` / explicit `TODO` comments in code.
- Project memory: `task_plan.md`, `findings.md`, `progress.md`, `LLM.md` (constitution).
- For a non-technical overview of the AI/agent tooling used to build this app, see
  `AI-AGENT-DEMO-SUMMARY.md`.
