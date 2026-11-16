# Arcade Game Forge

Turn a small game specification into a tested WASM app for
[Scratch Arcade OS](https://github.com/ayutaz/scratch-arcade-os).
Forge asks the local Codex CLI for C, checks the result against independent game
rules in two VMs, sends failures back for correction, and reproduces the package.

[日本語](README.ja.md)

## Current status

The host pipeline and failure handling pass tests. Real AI generation, playable
sample games and handheld deployment are being verified next. **This is not a
device-tested release.** Existing tests use a fake generator, real subprocesses,
the real WASM compiler, Wasmtime and WAMR. A compiling game can still fail.

The first version supports three closed game types: maze, falling-object dodge,
and coin collection. It does not generate arbitrary games or new OS features.

## Try it

Install [uv](https://docs.astral.sh/uv/), use an existing ChatGPT login in the
Codex CLI, and prepare the pinned OS SDK described in [setup](docs/setup.md).

```sh
uv sync --locked
uv run --locked python -m arcade_game_forge validate examples/specs/maze.json
uv run --locked python -m arcade_game_forge make examples/specs/maze.json \
  --sdk ../scratch-arcade-os --output runs/my-maze --attempts 3 --timeout 180
```

The command returns success only after independent tests and a matching rebuild.
Failed attempts remain in the local run directory. It never connects to a handheld.
Generation uses a read-only sandbox and a fresh workspace. API keys and paid API
fallback are disabled; no GPU is required.

## Tests

```sh
uv run --locked python -m unittest discover -s tests -v
# With the pinned OS SDK and Zig/WAMR sources available:
uv run --locked python -m unittest discover -s tests/integration -v
```

The default suite needs no model login, GPU or device. Integration tests compile
real WASM and check that a wrong game is rejected even when both VMs agree.

Read [game rules](docs/specification.md), [setup](docs/setup.md), and
[validation](docs/validation.md). Code is licensed under [Apache-2.0](LICENSE).
