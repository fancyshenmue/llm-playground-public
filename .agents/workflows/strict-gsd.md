---
description: Strict Get Shit Done (GSD) Development Workflow
---

# Strict Get Shit Done (GSD) Execution Workflow

This workflow ensures that no AI agent writes code before properly bounding the task within a structured GSD Phase. Whenever starting a new ticket or feature request, adhere strictly to the steps below:

**CRITICAL RULE:** All documentation generated during this workflow (CONTEXT, PLANS, ROADMAP updates, etc.) MUST be written in **English**. Do not use any other language for documentation.

1. **Information Gathering**
   - Read the user's request and ask any clarifying questions about their overall goal.
   - Do NOT modify any project files during this stage.

2. **Discuss Phase**
   - Execute the equivalent of `/gsd-discuss-phase`.
   - Document all architectural choices and task boundaries into a fresh Phase Context file: `.planning/phases/XX-<name>/XX-CONTEXT.md`.
   - **Check**: ALWAYS await user acknowledgment of the context before proceeding further.

3. **Plan Phase**
   - Execute the equivalent of `/gsd-plan-phase`.
   - Create a hyper-detailed, actionable checklist targeting exact files (e.g., `- [ ] 8a: Modify file.yaml`).
   - Output these checklist steps into `.planning/phases/XX-<name>/PLAN.md`.
   - **CRUCIAL STOP CHECK**: Immediately pause execution. Ask the user to accept the `PLAN.md` (e.g., "Say 'approved' to execute"). DO NOT write any functional code yet.

4. **Execution Phase**
   - Once explicit approval is granted, execute the equivalent of `/gsd-execute-phase`.
   - Begin modifying codebase files strictly conforming to the `PLAN.md` steps.
   - Track live progress by ticking off (`[x]`) items in `PLAN.md` before and after each sub-task modification.
   - **Service CLI Testing Policy**: You may execute service commands (e.g. `npm run dev`, `uvicorn`) in the background to verify features, but you MUST shut them down immediately after testing. Do not leave unattended service CLIs running.

5. **Documentation Audit & Closure Phase**
   - **MANDATORY**: After all code modifications are fully compiled, deployed, tested, and verified working by the user in the environment, ONLY THEN can you go back and update the documentation to reflect reality. Do not eagerly write or update documentation before the fix is actually verified.
   - **NEW COMPONENT RULE**: If the phase introduced a new service, application, or infrastructure component, you MUST create detailed `architecture.md` and `operations.md` documents within a dedicated folder under `documents/<component-name>/`. Furthermore, you MUST embed visual Mermaid.js architectural and sequence diagrams tracking network layout and data connections. When writing Mermaid diagrams, ALWAYS use `<br>` for newlines inside node text, never `\n`.
   - Edit `.planning/phases/XX-<name>/PLAN.md` to explicitly change all `- [ ]` into `- [x]` for executed tasks.
   - Append the completed sub-tasks and the full Phase summary with `✅ Completed` to `.planning/ROADMAP.md`.
   - Move the current phase to the "Work Completed" section in `.planning/STATE.md`.

6. **Small / Quick Fixes**
   - For trivially simple tasks (e.g. 1-2 line fixes, spelling corrections, minor YAML tweaks), skip the heavy full ceremony.
   - Use the Quick Task feature: quickly document the short plan inside a new directory at `.planning/quick/<id>-<desc>/<id>-PLAN.md`.
   - Execute the single change.
   - After execution, summarize the outcome in `<id>-SUMMARY.md` inside that same quick directory.
   - You MUST append a single entry representing the task to the "Quick Tasks Completed" table inside `.planning/STATE.md`.
