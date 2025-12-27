# Prompt CI/CD

AI-powered CI/CD pipeline generator from natural language prompts.

## Installation

```bash
pip install -e .
```

## Usage

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Generate CI/CD artifacts:

```bash
prompt-cicd generate --prompt "nodejs app with npm, port 3000" --output ./my-project
```

### Options

- `--prompt, -p`: Natural language description of your app (required)
- `--output, -o`: Output directory (default: `./output`)
- `--validate/--no-validate`: Validate generated artifacts (default: enabled)
- `--api-key`: OpenAI API key (or use `OPENAI_API_KEY` env var)

## Generated Artifacts

- `Dockerfile` - Multi-stage Docker build
- `.github/workflows/ci.yml` - GitHub Actions CI workflow

## Example

```bash
prompt-cicd generate \
  --prompt "A Node.js Express API using yarn, running on port 8080, with Jest tests" \
  --output ./my-api
```

This generates:
- A multi-stage Dockerfile optimized for Node.js
- A GitHub Actions workflow with build and test steps

## Development

```bash
pip install -e ".[dev]"
pytest
```
