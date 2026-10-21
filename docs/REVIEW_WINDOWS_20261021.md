# Windows release review: Claude / MCP

Reference: Matt Pocock Skills v1.3.1 (`code-review`, test-first bug correction).
Compared previous Windows build 39f1fe320234c2030287ac45a13e4571afc36417 with Claude/MCP implementation d129a9fcf0f36f638d84c053f8d3896c6ae86c03.

## Standards axis

- No project-specific coding standards file was present.
- Found: Gemini-only readiness prevented Claude-only startup. Corrected with provider-aware startup settings; fresh installations still show setup.
- Found: packaged verification did not exercise MCP. Added a credential-free loopback handshake, authorization, listing and execution check in the frozen executable.
- No additional Fowler smell finding justified a release-blocking refactor.

## Spec axis

- Claude typed startup now works without a Gemini key after selecting/saving Claude mode.
- Fish output in this release still needs the active Gemini Live session, as documented in the first-use guide. It is not independently available during a failed Gemini connection.
- Cancelled Fish workers are no longer retained across reconnects; active answer tasks are cancelled with their session.
- Native Claude Code installation/login, account access and Fish credentials remain user setup requirements, not bundled credentials.

## Validation

- 52 source tests passed, including the real MCP protocol test and three provider-readiness cases.
- New startup regression test was confirmed failing before implementation, then passing.
- The same MCP verification helper passed locally; the workflow must also run it from the actual Windows EXE.
- Windows frozen verification, artifact hash and installed dependency list are recorded by the build workflow.
- Live provider login, microphone, Fish voice, hardware and end-to-end latency remain unvalidated in CI.
