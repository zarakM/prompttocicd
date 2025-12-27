"""DevOps Agent using OpenAI Agents SDK."""

import os
from pathlib import Path
from agents import Agent, Runner

from prompt_cicd.tools import (
    generate_dockerfile,
    generate_ci_yaml,
    write_file,
    read_file,
    run_command,
    validate_dockerfile,
    validate_ci_yaml,
)

INSTRUCTIONS = """You are an autonomous DevOps Agent.
Your goal is to generate, validate, and fix CI/CD artifacts for the user's application.

### Workflow:

1. **Plan Phase**:
   - Analyze the user's request.
   - Plan which files need to be created (usually Dockerfile and CI YAML).

2. **Generation Phase**:
   - Use `generate_dockerfile` and `generate_ci_yaml` to create content.
   - Use `write_file` to save them to the specified output directory.
     - Dockerfile -> [output_dir]/Dockerfile
     - CI YAML -> [output_dir]/.github/workflows/ci.yml

3. **Validation & Fix Loop**:
   - For each generated file, run its validation tool:
     - `validate_dockerfile` for Dockerfiles
     - `validate_ci_yaml` for CI workflows
   - If validation FAILS:
     - Read the error message carefully.
     - Use `write_file` to overwrite the file with a fixed version.
     - Re-run validation.
     - Repeat up to 3 times.
   - If validation PASSES:
     - Proceed to the next file or finish.

4. **Completion**:
   - When all files are generated and validated (or max retries reached), report the final status.
   - List the files created and their validation status.

### Constraints:
- Always use the tools provided.
- Do not make up file content; use the generators.
- If you cannot fix an error after 3 tries, report the failure and stop.
"""

def create_agent(model: str = "gpt-4o") -> Agent:
    """Create and configure the DevOps agent."""
    return Agent(
        name="DevOps Agent",
        model=model,
        instructions=INSTRUCTIONS,
        tools=[
            generate_dockerfile,
            generate_ci_yaml,
            write_file,
            read_file,
            run_command,
            validate_dockerfile,
            validate_ci_yaml,
        ],
    )

def run_agent(prompt: str, output_dir: str, model: str = "gpt-4o", verbose: bool = False) -> str:
    """Run the agent synchronously.

    Args:
        prompt: User prompt.
        output_dir: Output directory path.
        model: Model to use.
        verbose: Whether to print detailed logs (handled by SDK tracing if enabled).

    Returns:
        Final output from the agent.
    """
    agent = create_agent(model)
    
    # Ensure output directory exists before starting
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Augment prompt with context
    full_prompt = (
        f"Goal: {prompt}\n"
        f"Output Directory: {output_dir}\n"
        "Please generate the artifacts, write them to disk, and validate them."
    )
    
    result = Runner.run_sync(agent, full_prompt)
    return result.final_output
