"""CLI for prompt-cicd using Click."""

import click
import os
import sys

from prompt_cicd import __version__
from prompt_cicd.agent import run_agent

# Import kept for non-agent commands if we wanted to keep them, 
# but per instructions we enter agent mode via `agent` command.
# We can keep `generate` as the "classic" non-agent mode if preferred, 
# or redirect it. For now, let's keep `generate` classic and `agent` for the new one.
from prompt_cicd.interpreter import IntentInterpreter
from prompt_cicd.generator import DockerfileGenerator, GitHubActionsGenerator
from prompt_cicd.writer import ArtifactWriter
from prompt_cicd.validator import ArtifactValidator


@click.group()
@click.version_option(version=__version__, prog_name="prompt-cicd")
def main():
    """AI-powered CI/CD pipeline generator from natural language prompts."""
    pass


@main.command()
@click.option(
    "--prompt",
    "-p",
    required=True,
    help="Natural language description of your application and CI/CD requirements.",
)
@click.option(
    "--output",
    "-o",
    default="./output",
    type=click.Path(),
    help="Output directory for generated artifacts.",
)
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key (or set OPENAI_API_KEY env var).",
)
def agent(prompt: str, output: str, api_key: str | None):
    """Run autonomous DevOps agent (powered by OpenAI Agents SDK).
    
    The agent will plan, generate, validate, and fix artifacts automatically.
    """
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    if "OPENAI_API_KEY" not in os.environ:
        click.echo("❌ Error: OPENAI_API_KEY not found. Please set it via env var or --api-key.")
        sys.exit(1)

    click.echo("🤖 Starting Autonomous DevOps Agent...")
    click.echo(f"   Prompt: {prompt}")
    click.echo(f"   Output: {output}")
    click.echo()

    try:
        final_output = run_agent(prompt, output)
        click.echo("\n✅ Agent finished execution.")
        click.echo("=" * 50)
        click.echo(final_output)
        click.echo("=" * 50)

    except Exception as e:
        click.echo(f"\n❌ Agent failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--prompt",
    "-p",
    required=True,
    help="Natural language description.",
)
@click.option(
    "--output",
    "-o",
    default="./output",
    type=click.Path(),
    help="Output directory.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Validate generated artifacts.",
)
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key.",
)
def generate(prompt: str, output: str, validate: bool, api_key: str | None):
    """(Classic) Generate CI/CD artifacts deterministically."""
    # Classic implementation preserved for reference/fallback
    click.echo(f"🚀 Generating CI/CD artifacts (Classic Mode)...")
    
    # ... (existing classic implementation logic)
    try:
        interpreter = IntentInterpreter(api_key=api_key)
        intent = interpreter.interpret(prompt)
    except Exception as e:
        click.echo(f"❌ Failed to interpret prompt: {e}", err=True)
        return

    generators = [DockerfileGenerator(), GitHubActionsGenerator()]
    writer = ArtifactWriter(output)
    
    generated_files = []
    for gen in generators:
        try:
            path = writer.write(gen, intent)
            generated_files.append((gen.filename, path))
            click.echo(f"   ✓ {gen.relative_path}")
        except Exception as e:
            click.echo(f"   ✗ {gen.filename}: {e}", err=True)

    if validate:
        validator = ArtifactValidator()
        for filename, path in generated_files:
            content = path.read_text()
            issues = []
            if filename == "Dockerfile":
                issues = validator.validate_dockerfile(content)
            elif filename == "ci.yml":
                issues = validator.validate_github_actions(content)
            
            if issues:
                click.echo(f"   ⚠ {filename}: {issues}")

    click.echo(f"✅ Done! Artifacts written to: {output}")


if __name__ == "__main__":
    main()
