# Flaky Test Analyzer

Built a Flaky Test Analyzer using Langflow + Groq — running locally 🛠️

## Demo Instructions
- Clone or open the Langflow flow on your local instance
- Upload your test results in JSON format (JUnit-compatible output works well)
- The pipeline parses the JSON and passes structured test data to the Groq LLM
- Groq analyzes the results and detects tests showing flaky behavior patterns
- Output: a clean list of flagged flaky tests — ready for your team to action

## Stack
- Orchestration: Langflow (local)
- LLM: Groq (fast inference)
- Input: JSON test result files
- Deployment: Fully local — no API costs, no data leaving your machine

## Key Technical Decisions
- Langflow chosen for rapid visual pipeline prototyping
- Groq used for near-instant inference on structured test data
- Local deployment ensures security for sensitive test logs

Building at the intersection of AI tooling and QA engineering — this is the kind of work I’m focused on right now.

Open to roles in QA Automation, AI-assisted testing, and process quality.

#QAAutomation #Langflow #Groq #FlakyTests #AIEngineering #SoftwareTesting #OpenToWork #LLM #TestAutomation
