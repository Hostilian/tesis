# Cross-repository toolchain — 22 November 2026

Repository: `Hostilian/tesis`. This document records **configuration**, not proof of authentication, completed reviews, deployments or API invocations.

## Tools and actual integration
- **Linear**: `.mcp.json` contains the official **read-only** MCP URL `https://mcp.linear.app/mcp/readonly`; OAuth authorization is still required. Use for requirements/issue context after login. No automatic Linear writes.
- **Mobbin MCP**: `.mcp.json` contains official `https://api.mobbin.com/mcp`; user authorizes on first use. Screens are design references, not source to copy.
- **Playwright MCP**: `.mcp.json` starts Microsoft's `@playwright/mcp` via npx; launch only from trusted sessions. Browser access is not proof a project's tests passed. For runnable browser tests add project-specific, verified `@playwright/test` specs.
- **CodeRabbit**: `.coderabbit.yaml` supplies review rules. The GitHub App must be authorized for each repo. Public-repo auto review is configured; official public GitHub review may be free once connected.
- **Greptile**: `.greptile/rules.md` supplies scoped reviewer guidance. Connect its GitHub app or CLI/login; verify credit limits before review. Never assume committed rules mean the reviewer ran.
- **Free reviewer**: `node scripts/free-review.mjs` checks tracked diffs; `--local-ai` optionally calls a **localhost-only Ollama** model (not installed/verified here), and `--codex` invokes your existing Codex account (subject to usage limits). No automated paid CI reviewer.
- **fal.ai**: `node scripts/media-gateway.mjs --provider fal --model fal-ai/flux/dev --prompt "test"` performs a **zero-network dry-run**. Real execution requires `--execute`, `ALLOW_PAID_MEDIA=YES`, `FAL_KEY` and the official `@fal-ai/client` installed for the workspace. Confirm the chosen model schema and price first.
- **Higgsfield**: the same media gateway supports `--provider higgsfield --model bytedance/seedance-2.0/text-to-video`; also dry-run by default. Real requests require `HF_API_KEY_ID`, `HF_API_KEY_SECRET` and the explicit paid gate. The sample payload targets that documented endpoint; other model schemas require adaptation.
- **Hermes Agent**: `scripts/agent-workspace.ps1 -Agent hermes` is a safe CLI entry point after separately installing/configuring official Nous Research Hermes. Not silently installed or logged into any model provider.
- **cmux**: the original cmux terminal is macOS-native; on the connected Windows laptop use `scripts/agent-workspace.ps1 -Agent codex` / `-Agent hermes` for the analogous repo-root agent session. This does **not** claim cmux itself is installed on Windows.

## Safety and verification
1. Review this repo's existing `AGENTS.md`, README, tests and confidentiality restrictions before use.
2. Run `node --check scripts/media-gateway.mjs` and `node --check scripts/free-review.mjs`, then `node scripts/media-gateway.mjs --provider fal --model fal-ai/flux/dev --prompt test` for a no-cost adapter smoke check.
3. Never commit keys, personal files, farm data or confidential screenshots to GitHub or send them to third-party review/media models. Do not enable paid provider requests without a separate explicit decision.
4. No emails, WhatsApp, Slack, applications, course submissions, invitations or externally shared documents may be sent by these integrations. No auto-merge or silent production deployment.
5. The operator must authenticate OAuth MCP servers and authorize GitHub review apps; file-level setup does not grant account permissions.

## Project-specific policy
Scientific reproducibility, satellite/aerial data provenance, publication safety; optional generated media is for clearly labeled explanation/demo only.

## Verified upstream references
- Linear: https://linear.app/docs/mcp
- Mobbin: https://github.com/mobbin/mobbin-mcp-server
- Playwright: https://playwright.dev/docs/getting-started-mcp
- CodeRabbit: https://www.coderabbit.ai/oss
- Greptile: https://www.greptile.com/docs/introduction
- Free PR-Agent alternative: https://github.com/The-PR-Agent/pr-agent
- Hermes: https://hermes-agent.nousresearch.com/docs/user-guide/windows-native
- cmux: https://cmux.com/
- fal client: https://github.com/fal-ai/fal-js
- Higgsfield: https://open.higgsfield.ai/quick-start
