# Project Tomo guidance for OpenAI Codex

This AGENTS.md file provides comprehensive guidance for OpenAI Codex and other AI agents working with this codebase.

## Project Structure for OpenAI Codex Navigation

### Root Layout
- `AGENTS.md`: agent guidance, rules, and workflow documentation.
- `.github/`: GitHub workflows, templates, and community health files.
- `backend/`: Python FastMCP server, tests, SQL helpers, and virtualenv.
- `frontend/`: Vite/React web client, Playwright tests, and configs.
- `docs/`: architecture notes, implementation plans, and reference guides.
- `docker/` & `docker-compose.dev.yml`: container definitions and local orchestration.
- `scripts/`: helper scripts for automation and maintenance tasks.
- `Makefile`: top-level task shortcuts for backend/frontend tooling.
- `README.md`: project overview and setup instructions.
- `venv/`: shared Python virtual environment (optional local usage).

### Backend (`backend/`)
- `src/`: FastMCP backend code.
  - `main.py`: entry point that wires services and logging.
  - `services/`: application service layer (auth, app, monitoring, etc.).
  - `tools/`: FastMCP tool registrations grouped by domain.
- `lib/`: shared helpers such as logging configuration and encryption.
  - `config/`, `database/`, `models/`, `exceptions/`: configuration, persistence, data models, and custom errors.
- `tests/`: unit, integration, and security suites plus fixtures.
- `sql/`: raw SQL helpers and seeds.
- `data/`: runtime data (e.g., exported artifacts).
- `venv/`: local Python virtual environment.

### Frontend (`frontend/`)
- `src/`: React + Vite application code.
  - `components/`, `pages/`, `hooks/`, `providers/`: UI composition and state layers.
- `services/`, `utils/`, `data/`, `types/`, `styles/`: API clients, helpers, static assets, typings, and styling.
  - `test/`: component-level utilities and mocks.
- `tests/`: Playwright end-to-end specs and screenshots.
- `playwright-report/`: latest Playwright HTML reports.
- `vite.config.ts`, `vitest.config.ts`, `tailwind.config.js`: build and tooling configuration.
- `package.json`, `yarn.lock`: Yarn dependency manifests.


## Operating Rules for Codex Agents

### 1. Environment & Tooling

**Backend (Python)**
- Activate the virtualenv before running backend tooling: `cd backend && source venv/bin/activate`.
- Bootstrap dependencies: `make install-deps` or `cd backend && pip install -e ".[dev]"`.
- Start the MCP server with `make start-backend` (activates the backend virtualenv and runs `python src/main.py`).

**Frontend (React/Yarn)**
- Activate the virtualenv before running frontend tooling: `source venv/bin/activate`.
- Install dependencies with Yarn (canonical manager): `cd frontend && yarn install --frozen-lockfile`.
- Start the dev server with `make start-frontend` (wraps `yarn dev`); run one-off scripts via `yarn <task>`.
- Do not commit `package-lock.json`; Yarn (`yarn.lock`) governs dependency state.

### 2. Core Principles

**Shared**
- Add tests and documentation when changes warrant them.
- Keep files and functions at or below 120 lines.
- Engage the right agent roles for each milestone; do not skip required approvals.
- Use structured logging, avoid secrets in logs, prefer simple solutions, and record major decisions.
- Favor straightforward implementations; avoid unnecessary complexity when a simpler option exists.
- Run the published quality commands before submitting work (`make backend-lint`, `make backend-format`, `make frontend-lint`, `make frontend-format`, `make typecheck`).
- Never run `git commit` or `git push`; source control commits are user-owned.
- For any backend or frontend feature work, update the implementation plan and architecture documentation under `docs/`.
- Review code for clarity and maintainability—prefer small, composable modules over monoliths.
- Continuously retire dead code and keep dependencies patched and minimal.

**Backend**
- Must Absolutely Follow the Google Python Style Guide (https://google.github.io/styleguide/pyguide.html).
- Guard credentials/PII in logs and errors; ensure allowlists on privileged tool actions.
- Maintain server-side validation on tool inputs/outputs and database interactions.
- Embrace type hints and dataclasses/pydantic models to document intent and catch regressions.
- Favor pure functions where possible; isolate side-effects behind service interfaces.
- Ensure migrations and seeds remain idempotent and reversible.

**Frontend**
- Follow React best practices (hooks rules, dependency arrays, accessibility, composition).
- Validate client payloads (e.g., with zod) before invoking tools or APIs.
- Preserve keyboard accessibility and graceful handling of slow or offline states.
- Keep components typed (TypeScript strict mode) and colocate tests/stories with UI code.
- Avoid prop drilling by composing context/providers judiciously; document shared hooks.
- Guard network edges with retry/cancellation patterns and surface actionable errors to the user.
- Use Yarn for all dependency updates and scripts to keep `yarn.lock` authoritative.

### 3. Streaming & Interrupts
- Use incremental SSE parsing (avoid `await response.text()`); emit tokens as they arrive.
- Thread `AbortController` from client to server so tools can cancel safely.

### 4. Validation & Error Handling
- Validate tool inputs with zod on the client and schema checks on the server.
- Normalize errors to `{ code, message, cause? }`; retry transient 429/5xx with capped backoff and jitter.

### 5. Testing Expectations
- Provide unit tests for logic, component tests for UI, and E2E tests for flows.
- QA Tester owns suite design; QA Lead verifies coverage before release.

### 6. Security & Privacy
- Security Auditor must review authentication, privacy, and data handling changes.
- Never expose provider secrets in the browser; allowlist tool names and actions.

### 7. Reference Snippet
```ts
export async function streamResponse(url: string, body: unknown, signal: AbortSignal, onToken: (chunk: string) => void) {
  const res = await fetch(url, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
    signal
  })
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    onToken(decoder.decode(value, { stream: true }))
  }
}
```

## Team Roles

**Role Declaration**
- At the start of each scoped task, the active agent must state which role persona they are operating under so collaborators understand the perspective driving the work.

- **Product Owner**
  - Owns product vision, roadmap, and acceptance criteria.
  - Partners with Tech Writer and Dev Lead to time releases.
- **Architect**
  - Produces solution designs and decision logs.
  - Coordinates with the MCP Specialist to keep the platform compliant.
- **Developer**
  - Implements scoped backlog items and keeps files/functions within limits.
  - Flags risks early to the Architect, Security Auditor, or Dev Lead.
- **Security Auditor**
  - Performs threat analysis for auth/privacy/data flows.
  - Approves mitigations prior to release.
- **QA Tester**
  - Drafts and automates unit, component, and E2E suites.
  - Supplies reproduction details for every defect.
- **QA Lead**
  - Aggregates test evidence, tracks quality KPIs, and owns release sign-off.
  - Verifies Definition of Done using the operating rules above.
- **Tech Writer**
  - Updates documentation, changelogs, and release notes.
  - Confirms messaging with Product Owner and Dev Lead.
- **Dev Lead**
  - Manages delivery cadence and removes blockers.
  - Ensures dependencies across roles are addressed before launch.
- **MCP Specialist**
  - Owns FastMCP protocol adherence and tool schema quality.
  - Guides streaming, interrupts, and validation strategies.
- **Site Reliability / DevOps** *(optional but recommended)*
  - Monitors deployment health and maintains runbooks.
  - Shares incident learnings with the wider team.

## Collaboration Workflow

1. Product Owner confirms scope and acceptance criteria.
2. Architect drafts the design and aligns with the MCP Specialist.
3. Developer implements, coordinating with the MCP Specialist and preparing security evidence.
4. Security Auditor reviews auth/privacy/data impacts, validates mitigations, and signs off.
5. QA Tester executes suites; QA Lead reviews and signs off.
6. Tech Writer finalises documentation; Dev Lead coordinates release readiness.
