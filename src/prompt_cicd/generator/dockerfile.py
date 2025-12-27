"""Dockerfile generator using Jinja2 templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from prompt_cicd.interpreter import DevOpsIntent
from prompt_cicd.generator.base import BaseGenerator


class DockerfileGenerator(BaseGenerator):
    """Generate Dockerfile from DevOps intent using Jinja2 templates."""
    
    def __init__(self):
        """Initialize the generator with template environment."""
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template = self.env.get_template("dockerfile.j2")
    
    @property
    def filename(self) -> str:
        """Return the filename for this artifact."""
        return "Dockerfile"
    
    @property
    def relative_path(self) -> str:
        """Return the relative path for this artifact."""
        return "Dockerfile"
    
    def generate(self, intent: DevOpsIntent) -> str:
        """
        Generate Dockerfile content from DevOps intent.
        
        Args:
            intent: Structured DevOps intent
            
        Returns:
            Dockerfile content as string
        """
        # Convert intent to template context
        context = {
            "language": intent.language,
            "runtime": intent.runtime,
            "runtime_version": intent.runtime_version,
            "build_tool": intent.build_tool,
            "build_command": intent.build_command,
            "test_command": intent.test_command,
            "expose_port": intent.expose_port,
            "package_manager_lock_file": intent.package_manager_lock_file,
        }
        
        return self.template.render(**context)
