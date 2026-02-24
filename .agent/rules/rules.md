# llm-playground Coding Rules & Standards

To ensure high code quality and consistency across this polyglot project, follow these rules:

## General Principles
- **Pixi First**: All dependencies and environment management must go through `pixi.toml`. Do not run `pip install` or `npm install` directly outside of the Pixi environment.
- **Run with Pixi**: Always use `pixi run <task>` to execute project-specific scripts, tests, or builds. Verification MUST be done via [pixi run test](file://$HOME/dev/llm-playground/pixi.toml).
- **Modular Rules**: Detailed rules for specific areas are located in [rules/](file://$HOME/dev/llm-playground/.agent/rules/). See [testing.md](file://$HOME/dev/llm-playground/.agent/rules/testing.md) for verification standards.
- **Documentation**: New features must be documented in `documents/` and reflected in `.agent/project_map.json` if they change the project structure.
- **Context Awareness**: Always check `.agent/config.json` for caching strategies.

## Go (Golang)
- **CLI Framework**: Use `spf13/cobra` for all CLI commands in `cmd/go/`.
- **Project Structure**: Follow the `cmd/` and `internal/` pattern. Logic that shouldn't be exported must reside in `internal/`.
- **Error Handling**: Explicit error handling is mandatory. Avoid `panic` unless absolutely necessary.

## Python
- **Environment**: Use Python 3.10.11 (as defined in `pixi.toml`).
- **Type Hinting**: All new functions must have type hints.
- **GPU Usage**: When writing scripts that use the GPU, check for CUDA availability and respect the `check-gpu` task convention.

## Web & Designing (Node.js/CSS)
- **Aesthetics**: Prioritize "WOW" factor. Use modern HSL color palettes and smooth transitions.
- **Tailwind**: Do not use Tailwind unless explicitly asked. Use Vanilla CSS with a strong design system.
- **Interactivity**: Micro-animations and hover effects should be used to make the UI feel "alive".

## RAG & Data Handling
- **Data Formats**: Use JSON/YAML for shared data between tools.
- **Atomic Operations**: Ensure data generation and tagging are idempotent where possible.
