"""Artifact writer for writing generated content to the filesystem."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prompt_cicd.generator.base import BaseGenerator
    from prompt_cicd.interpreter import DevOpsIntent


class ArtifactWriter:
    """Write generated artifacts to the output directory."""

    def __init__(self, output_dir: str | Path):
        """Initialize the writer with an output directory.

        Args:
            output_dir: Directory to write artifacts to.
        """
        self.output_dir = Path(output_dir)

    def write(self, generator: "BaseGenerator", intent: "DevOpsIntent") -> Path:
        """Generate and write an artifact to disk.

        Args:
            generator: The generator to use for creating content.
            intent: The DevOps intent to generate from.

        Returns:
            The path to the written file.
        """
        # Generate the content
        content = generator.generate(intent)

        # Determine output path
        output_path = self.output_dir / generator.relative_path

        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        output_path.write_text(content)

        return output_path

    def write_all(
        self, generators: list["BaseGenerator"], intent: "DevOpsIntent"
    ) -> list[Path]:
        """Generate and write all artifacts.

        Args:
            generators: List of generators to use.
            intent: The DevOps intent to generate from.

        Returns:
            List of paths to written files.
        """
        return [self.write(gen, intent) for gen in generators]
