"""Artifact testing agent for validating generated CI/CD artifacts."""

import subprocess
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TestResult:
    """Result of an artifact test."""

    artifact: str
    success: bool
    message: str
    details: list[str] = field(default_factory=list)


class ArtifactTestingAgent:
    """Test generated CI/CD artifacts by executing them."""

    def __init__(self, verbose: bool = False):
        """Initialize the testing agent.

        Args:
            verbose: If True, print detailed output during tests.
        """
        self.verbose = verbose

    def _run_command(
        self, cmd: list[str], cwd: Optional[Path] = None
    ) -> tuple[int, str, str]:
        """Run a command and capture output.

        Args:
            cmd: Command and arguments to run.
            cwd: Working directory for the command.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 5 minutes"
        except FileNotFoundError:
            return -1, "", f"Command not found: {cmd[0]}"

    def test_dockerfile(
        self, dockerfile_path: Path, image_name: str = "prompt-cicd-test"
    ) -> TestResult:
        """Test a Dockerfile by building an image.

        Args:
            dockerfile_path: Path to the Dockerfile.
            image_name: Name for the test image.

        Returns:
            TestResult with build status.
        """
        if not dockerfile_path.exists():
            return TestResult(
                artifact="Dockerfile",
                success=False,
                message="Dockerfile not found",
                details=[str(dockerfile_path)],
            )

        # Check if Docker is available
        if not shutil.which("docker"):
            return TestResult(
                artifact="Dockerfile",
                success=False,
                message="Docker is not installed or not in PATH",
                details=["Install Docker to test Dockerfile builds"],
            )

        # Build the image
        build_context = dockerfile_path.parent
        cmd = [
            "docker",
            "build",
            "-t",
            image_name,
            "-f",
            str(dockerfile_path),
            str(build_context),
        ]

        if self.verbose:
            print(f"Running: {' '.join(cmd)}")

        returncode, stdout, stderr = self._run_command(cmd)

        if returncode == 0:
            # Clean up the test image
            cleanup_cmd = ["docker", "rmi", image_name, "-f"]
            self._run_command(cleanup_cmd)

            return TestResult(
                artifact="Dockerfile",
                success=True,
                message="Docker image built successfully",
                details=["Image built and cleaned up"],
            )
        else:
            # Extract error details
            error_lines = []
            for line in (stderr + stdout).split("\n"):
                if "error" in line.lower() or "failed" in line.lower():
                    error_lines.append(line.strip())

            return TestResult(
                artifact="Dockerfile",
                success=False,
                message="Docker build failed",
                details=error_lines[:10] if error_lines else [stderr[:500]],
            )

    def test_github_actions(self, workflow_path: Path) -> TestResult:
        """Test a GitHub Actions workflow using actionlint.

        Args:
            workflow_path: Path to the workflow YAML file.

        Returns:
            TestResult with validation status.
        """
        if not workflow_path.exists():
            return TestResult(
                artifact="GitHub Actions",
                success=False,
                message="Workflow file not found",
                details=[str(workflow_path)],
            )

        # Check if actionlint is available
        if not shutil.which("actionlint"):
            return TestResult(
                artifact="GitHub Actions",
                success=False,
                message="actionlint is not installed",
                details=[
                    "Install with: brew install actionlint",
                    "Or: go install github.com/rhysd/actionlint/cmd/actionlint@latest",
                ],
            )

        cmd = ["actionlint", str(workflow_path)]

        if self.verbose:
            print(f"Running: {' '.join(cmd)}")

        returncode, stdout, stderr = self._run_command(cmd)

        if returncode == 0:
            return TestResult(
                artifact="GitHub Actions",
                success=True,
                message="Workflow passed actionlint validation",
            )
        else:
            # Parse actionlint output for issues
            issues = []
            for line in (stdout + stderr).split("\n"):
                line = line.strip()
                if line and not line.startswith("actionlint"):
                    issues.append(line)

            return TestResult(
                artifact="GitHub Actions",
                success=False,
                message="Workflow has actionlint errors",
                details=issues[:10],
            )

    def test_all(self, output_dir: Path) -> list[TestResult]:
        """Test all artifacts in an output directory.

        Args:
            output_dir: Directory containing generated artifacts.

        Returns:
            List of TestResult for each artifact.
        """
        results = []
        output_path = Path(output_dir)

        # Test Dockerfile
        dockerfile_path = output_path / "Dockerfile"
        if dockerfile_path.exists():
            results.append(self.test_dockerfile(dockerfile_path))

        # Test GitHub Actions workflow
        workflow_path = output_path / ".github" / "workflows" / "ci.yml"
        if workflow_path.exists():
            results.append(self.test_github_actions(workflow_path))

        return results
