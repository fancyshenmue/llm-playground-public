# Testing Rules

To maintain code reliability and environment consistency, all testing and verification must be performed using `pixi`.

## Mandatory Testing Workflow

1. **Always use Pixi**: Never run `go test`, `npm test`, or `pytest` directly. Always use the corresponding `pixi run` task.
2. **Pre-commit Verification**: Before submitting any code changes, ensure they pass the relevant `pixi` verification tasks.
3. **Available Tasks**:
   - `pixi run test`: Runs all tests across the project.
   - `pixi run test-go`: Runs Go-specific tests.
   - `pixi run test-node`: Runs Node.js-specific verification (linting, typechecking, and tests).

## Rationale
Using `pixi` ensures that all tests are run within the correctly configured environment with the exact dependency versions specified in `pixi.toml`, preventing "works on my machine" issues.
