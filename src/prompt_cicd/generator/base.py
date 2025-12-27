"""Base generator abstract class."""

from abc import ABC, abstractmethod

from prompt_cicd.interpreter import DevOpsIntent


class BaseGenerator(ABC):
    """Abstract base class for CI/CD artifact generators."""

    @property
    @abstractmethod
    def filename(self) -> str:
        """Return the filename for this artifact.

        Returns:
            The filename (e.g., "Dockerfile", "ci.yml")
        """
        pass

    @property
    @abstractmethod
    def relative_path(self) -> str:
        """Return the relative path for this artifact from the output directory.

        Returns:
            The relative path (e.g., "Dockerfile", ".github/workflows/ci.yml")
        """
        pass

    @abstractmethod
    def generate(self, intent: DevOpsIntent) -> str:
        """Generate the artifact content from DevOps intent.

        Args:
            intent: Structured DevOps intent from the interpreter.

        Returns:
            The generated artifact content as a string.
        """
        pass
