# Demo Summary: AI Agent Tooling Behind This Build

A one-page reference for presenting **how** this app was built, not just what it does. Two layers of
AI are involved: the **agent that built the app** (Claude Code) and the **agents the app itself calls**
(the LLM providers it integrates).

## 1. The build process: "vibe coding" with an agentic CLI

**Tool**: Claude Code (Anthropic), running as a VS Code-integrated agent in this session.

Unlike a chat-based code assistant (paste code, copy back), Claude Code operates as an **autonomous
agent with direct tool access** — it reads files, edits them, runs shell commands, starts/stops
servers, and verifies its own output, in a loop, without a human relaying information back and forth.

What that looked like concretely in this build:

| Capability | What happened in this project |
|---|---|
| **Planning before coding** | For the initial multi-mode feature (mode picker, Test Cases, Test Scripts, multi-provider Settings), the agent entered a read-only **plan mode**: explored the existing codebase, asked clarifying questions (phasing, which providers, real vs. stubbed Azure DevOps integration), then wrote a concrete file-by-file plan for approval *before* touching code. |
| **Multi-file implementation** | Built ~20 new/changed files in one pass: 6 backend `tools/` modules, 3 new API endpoints (mirrored across Express + Vercel serverless), 8 new React components, CSS, and config — while keeping the original Test Plan flow byte-for-byte backward compatible. |
| **Self-verification, not just code generation** | After writing code, the agent ran `vite build` to catch compile errors, started the actual dev server, and hit every new API endpoint with real `curl` calls against the user's live Jira + GROQ credentials — catching a Jira-auth break and a GROQ JSON-validation crash *before* the user ever saw them. |
| **Root-causing real failures, live** | When TestNG/Java script generation failed in production use, the agent diagnosed two distinct issues from a single error message: (1) embedding Java source inside strict JSON responses breaks LLM JSON-mode validators — fixed by switching to a delimited plain-text output format; (2) GROQ's free-tier 8000-token/minute cap was being exceeded by one large request — fixed by generating one file per test case with automatic retry honoring the provider's own backoff hint. |
| **Treating credentials as real secrets** | When the user pasted what was labeled a "Jira token" but was clearly shaped like an OpenAI key, the agent flagged the mismatch, asked for confirmation rather than guessing, tested empirically (the value broke real Jira auth), and corrected the `.env` mapping — instead of silently trusting a mislabeled input. |
| **Leaving reusable artifacts behind** | Beyond the app code, the agent authored a project-scoped **Claude Code Skill** (`.claude/skills/run-app/SKILL.md`) so future sessions — human or agent — can restart the dev server, clear stale Windows port locks, and smoke-test every mode without rediscovering the same friction points. |

**Demo talking point**: this is the difference between "AI writes a function" and "AI agent owns a
feature end-to-end" — plan, build, run, test against real APIs, debug live failures, document the
result.

## 2. The product itself: multi-agent / multi-provider orchestration

The app is a small example of **agent orchestration with a pluggable model layer**:

```
                    ┌─────────────────────────────────────────┐
   Jira ticket  ───►│  tools/ticketSource.js                   │
   or Azure        │  (Jira REST  or  Azure DevOps REST)       │
   DevOps item      └───────────────┬───────────────────────────┘
                                     ▼
                    ┌─────────────────────────────────────────┐
                    │  tools/llmClient.js                       │
                    │  one call signature → 4 providers:        │
                    │   GROQ · OpenAI · Anthropic · Azure OpenAI│
                    └───────────────┬───────────────────────────┘
                       ┌────────────┼────────────┐
                       ▼            ▼             ▼
                 Test Plan     Test Cases    Test Scripts
                 (Markdown)  (structured    (Python/Java
                              JSON table)    source files)
```

Key engineering decisions worth calling out in a demo:

- **Provider-agnostic core**: switching the active LLM (GROQ → OpenAI → Anthropic → Azure OpenAI) is a
  Settings toggle, not a code change — each provider's different auth/endpoint/response shape is
  normalized behind one `chat()` function.
- **Deterministic boundary between AI and code**: the LLM only ever produces *content* (plan JSON, test
  case rows, source code text). Markdown rendering, table parsing, CSV/XLSX export, and ZIP packaging
  are all plain deterministic code — the AI is never asked to also "format the output correctly," which
  is where most LLM-output bugs come from.
- **Right-sizing requests to the model**: large multi-file code-generation requests are split into many
  small ones rather than one giant call — smaller blast radius per failure, avoids provider output-token
  truncation, and avoids the exact JSON-escaping fragility that broke the first version of Test Scripts.
- **Graceful degradation under rate limits**: when a provider's free-tier throughput cap is hit
  mid-batch, the app retries using the provider's own suggested backoff and returns partial results
  with a clear per-item error list — never a silent failure or a hard crash.

## Suggested demo flow

1. Show the mode picker → generate a **Test Plan** from a real Jira ticket (fast, single LLM call).
2. Generate **Test Cases** from the same ticket, then upload a sample `.xlsx` and show the output
   matching its column structure.
3. Hit **"Use these test cases"** → generate **Test Scripts** in TestNG (Java) → point out the
   per-file generation log taking longer for 8 files (real rate-limit handling, not a stall).
4. Switch the active provider in Settings (e.g. GROQ → OpenAI) and re-run one mode to show the
   provider-agnostic core.
5. Close with the `.claude/skills/run-app/SKILL.md` file as the "documentation the agent wrote for
   itself" — a concrete artifact of agentic development practice, not just shipped product code.
