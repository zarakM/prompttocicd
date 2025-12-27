"""GitHub Actions workflow generator using Jinja2 templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from prompt_cicd.interpreter import DevOpsIntent
from prompt_cicd.generator.base import BaseGenerator


class GitHubActionsGenerator(BaseGenerator):
    """Generate GitHub Actions workflow from DevOps intent using Jinja2 templates."""

    def __init__(self):
        """Initialize the generator with template environment."""
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template = self.env.get_template("github_actions.j2")

    @property
    def filename(self) -> str:
        """Return the filename for this artifact."""
        return "ci.yml"

    @property
    def relative_path(self) -> str:
        """Return the relative path for this artifact."""
        return ".github/workflows/ci.yml"

    def generate(self, intent: DevOpsIntent) -> str:
        """
        Generate GitHub Actions workflow content from DevOps intent.

        Args:
            intent: Structured DevOps intent

        Returns:
            GitHub Actions workflow content as string
        """
        context = {
            "language": intent.language,
            "runtime": intent.runtime,
            "runtime_version": intent.runtime_version,
            "build_tool": intent.build_tool,
            "build_command": intent.build_command,
            "test_command": intent.test_command,
        }

        return self.template.render(**context)
