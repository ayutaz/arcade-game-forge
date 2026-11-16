# Development rules

- Inspect git status and this file before edits; preserve unrelated changes.
- Use uv, Python 3.12.13 and the lockfile. No pip or manual virtual environments.
- Behavioral changes use intended Red before implementation, then Green and regression. Record commands/results in Japanese docs. Do not label later verification as TDD.
- Generated games must pass the independent contract evaluator; do not edit the evaluator to accept a failing game. Preserve failed attempts and distinguish initial/repaired success.
- Keep evaluation input sequences out of generator prompts. Never describe a three-spec evaluation as a general generation success rate.
- A Codex invocation is a bounded product integration test, not a general delegation task. Use read-only sandbox, explicit workspace, structured output, finite deadlines and no protection bypass. Do not pass secrets or private Lab material to generation.
- No paid OpenAI/other API or GPU calls in the initial release. Existing local CLI authentication is the only model connection. Record actual model failures rather than silently switching to hand-written games.
- English README is default; keep Japanese README aligned. Separate host/target/device/human evidence.
- No raw firmware, recordings, keys or hardware identifiers in Git. Dedicated app changes need ownership/hash guards and preservation of unrelated apps. New firmware/unknown GPIO/security changes require a concrete review and individual permission.
- Shared OS/SDK changes go through scratch-arcade-os PR and required CI. Keep this repo main protected after initial setup; use PR and passing checks for later changes.
- Commit focused validated changes and push. No force-push or history rewriting.
