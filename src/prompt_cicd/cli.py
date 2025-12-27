"""CLI for prompt-cicd using Click."""

import click
from pathlib import Path

from prompt_cicd import __version__
from prompt_cicd.interpreter import IntentInterpreter
from prompt_cicd.generator import DockerfileGenerator, GitHubActionsGenerator
from prompt_cicd.writer import ArtifactWriter
from prompt_cicd.validator import ArtifactValidator
from prompt_cicd.agent import ArtifactTestingAgent


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
    "--validate/--no-validate",
    default=True,
    help="Validate generated artifacts.",
)
@click.option(
    "--test/--no-test",
    default=False,
    help="Test artifacts by building Docker image and running actionlint.",
)
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key (or set OPENAI_API_KEY env var).",
)
def generate(prompt: str, output: str, validate: bool, test: bool, api_key: str | None):
    """Generate CI/CD artifacts from a natural language prompt."""
    click.echo(f"🚀 Generating CI/CD artifacts...")
    click.echo(f"   Prompt: {prompt[:50]}..." if len(prompt) > 50 else f"   Prompt: {prompt}")
    click.echo()

    # Parse the prompt into structured intent
    click.echo("📝 Interpreting prompt...")
    try:
        interpreter = IntentInterpreter(api_key=api_key)
        intent = interpreter.interpret(prompt)
    except Exception as e:
        click.echo(f"❌ Failed to interpret prompt: {e}", err=True)
        raise click.Abort()

    click.echo(f"   Language: {intent.language}")
    click.echo(f"   Runtime: {intent.runtime} {intent.runtime_version}")
    click.echo(f"   Build tool: {intent.build_tool or 'default'}")
    click.echo()

    # Set up generators
    generators = [
        DockerfileGenerator(),
        GitHubActionsGenerator(),
    ]

    # Generate and write artifacts
    click.echo("🔧 Generating artifacts...")
    writer = ArtifactWriter(output)
    
    generated_files = []
    for gen in generators:
        try:
            path = writer.write(gen, intent)
            generated_files.append((gen.filename, path))
            click.echo(f"   ✓ {gen.relative_path}")
        except Exception as e:
            click.echo(f"   ✗ {gen.filename}: {e}", err=True)

    click.echo()

    # Validate if requested
    if validate:
        click.echo("🔍 Validating artifacts...")
        validator = ArtifactValidator()
        
        for filename, path in generated_files:
            content = path.read_text()
            
            if filename == "Dockerfile":
                issues = validator.validate_dockerfile(content)
            elif filename == "ci.yml":
                issues = validator.validate_github_actions(content)
            else:
                issues = []
            
            if issues:
                click.echo(f"   ⚠ {filename}:")
                for issue in issues:
                    click.echo(f"      - {issue}")
            else:
                click.echo(f"   ✓ {filename}")
        
        click.echo()

    # Test if requested
    if test:
        _run_tests(Path(output))

    click.echo(f"✅ Done! Artifacts written to: {output}")


def _run_tests(output_dir: Path, verbose: bool = False):
    """Run artifact tests and display results."""
    click.echo("🧪 Testing artifacts...")
    agent = ArtifactTestingAgent(verbose=verbose)
    results = agent.test_all(output_dir)

    for result in results:
        if result.success:
            click.echo(f"   ✓ {result.artifact}: {result.message}")
        else:
            click.echo(f"   ✗ {result.artifact}: {result.message}")
            for detail in result.details:
                click.echo(f"      - {detail}")
    
    click.echo()


@main.command()
@click.argument("output_dir", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output.")
def test(output_dir: str, verbose: bool):
    """Test generated artifacts in OUTPUT_DIR.
    
    Tests Dockerfile by building an image and GitHub Actions workflow using actionlint.
    """
    click.echo(f"🧪 Testing artifacts in: {output_dir}")
    click.echo()
    
    _run_tests(Path(output_dir), verbose=verbose)
    
    click.echo("✅ Testing complete!")


if __name__ == "__main__":
    main()
