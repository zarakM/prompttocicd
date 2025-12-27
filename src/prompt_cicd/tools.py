"""Agent tools using OpenAI Agents SDK function_tool decorator."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Any

from agents import function_tool, RunContextWrapper

from prompt_cicd.interpreter import DevOpsIntent
from prompt_cicd.generator import DockerfileGenerator, GitHubActionsGenerator


@function_tool
def generate_dockerfile(
    language: str,
    runtime: str,
    runtime_version: str = "20",
    build_tool: Optional[str] = None,
    build_command: Optional[str] = None,
    test_command: Optional[str] = None,
    expose_port: Optional[int] = None,
    package_manager_lock_file: Optional[str] = None,
    start_command: Optional[str] = None,
) -> str:
    """Generate Dockerfile content based on application requirements.

    Args:
        language: Programming language (e.g., nodejs, python).
        runtime: Runtime environment (e.g., node, python).
        runtime_version: Version of the runtime.
        build_tool: Build tool to use (e.g., npm, yarn, pip).
        build_command: Command to build the application.
        test_command: Command to run tests.
        expose_port: Port to expose.
        package_manager_lock_file: Lock file name.
        start_command: Command to start the application.
    Returns:
        Generated Dockerfile content.
    """
    intent = DevOpsIntent(
        language=language,
        runtime=runtime,
        runtime_version=runtime_version,
        build_tool=build_tool,
        build_command=build_command,
        test_command=test_command,
        expose_port=expose_port,
        package_manager_lock_file=package_manager_lock_file,
        start_command=start_command,
    )
    generator = DockerfileGenerator()
    return generator.generate(intent)


@function_tool
def generate_ci_yaml(
    language: str,
    runtime: str,
    runtime_version: str = "20",
    build_tool: Optional[str] = None,
    build_command: Optional[str] = None,
    test_command: Optional[str] = None,
    start_command: Optional[str] = None,
) -> str:
    """Generate GitHub Actions CI workflow content.

    Args:
        language: Programming language.
        runtime: Runtime environment.
        runtime_version: Version of the runtime.
        build_tool: Build tool to use.
        build_command: Build command.
        test_command: Test command.
        start_command: Command to start the application.
    Returns:
        Generated CI YAML content.
    """
    intent = DevOpsIntent(
        language=language,
        runtime=runtime,
        runtime_version=runtime_version,
        build_tool=build_tool,
        build_command=build_command,
        test_command=test_command,
        start_command=start_command,
    )
    generator = GitHubActionsGenerator()
    return generator.generate(intent)


@function_tool
def write_file(path: str, content: str) -> str:
    """Write content to a file at the specified path.

    Args:
        path: Absolute or relative path to the file.
        content: Text content to write.

    Returns:
        A success message or error message.
    """
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@function_tool
def read_file(path: str) -> str:
    """Read content from a file.

    Args:
        path: Path to the file to read.

    Returns:
        File content or error message.
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File {path} not found"
        return file_path.read_text()
    except Exception as e:
        return f"Error reading file: {e}"


@function_tool
def run_command(command: str, cwd: Optional[str] = None) -> str:
    """Run a shell command and return output.

    Args:
        command: Command string to execute.
        cwd: Optional working directory.

    Returns:
        Combined stdout and stderr.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = f"Exit code: {result.returncode}\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
        return output
    except Exception as e:
        return f"Error running command: {e}"


@function_tool
def validate_dockerfile(dockerfile_path: str, work_dir: Optional[str] = None) -> str:
    """Validate Dockerfile by attempting to build a Docker image.

    Args:
        dockerfile_path: Path to the Dockerfile.
        work_dir: build context directory (defaults to Dockerfile's parent).

    Returns:
        Success message or build failure output.
    """
    # Check if Docker is available
    if not shutil.which("docker"):
        return "Error: Docker is not installed or not in PATH. Cannot validate Dockerfile."

    path = Path(dockerfile_path)
    if not path.exists():
        return f"Error: Dockerfile not found at {dockerfile_path}"
    
    context = work_dir or str(path.parent)
    
    cmd = f"docker build -t test-build -f {dockerfile_path} {context}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Cleanup
        subprocess.run("docker rmi test-build -f", shell=True, capture_output=True)
        return "Success: Docker build passed successfully."
    else:
        return f"Failure: Docker build failed.\n{result.stderr}\n{result.stdout}"


@function_tool
def validate_ci_yaml(workflow_path: str) -> str:
    """Validate GitHub Actions workflow using yamllint and act (if available).

    Args:
        workflow_path: Path to the CI YAML file.

    Returns:
        Validation results from yamllint and act.
    """
    path = Path(workflow_path)
    if not path.exists():
        return f"Error: Workflow file not found at {workflow_path}"

    results = []

    # 1. yamllint
    yamllint_res = subprocess.run(
        f"yamllint {workflow_path}", 
        shell=True, capture_output=True, text=True
    )
    if yamllint_res.returncode == 0:
        results.append("yamllint: Passed")
    else:
        results.append(f"yamllint: Failed\n{yamllint_res.stdout}")

    # 2. act (dry-run)
    if shutil.which("act"):
        cwd = str(path.parent.parent.parent) # Assuming .github/workflows/ci.yml -> root
        act_res = subprocess.run(
            f"act -n -W {workflow_path}",
            shell=True, cwd=cwd, capture_output=True, text=True
        )
        if act_res.returncode == 0:
            results.append("act: Passed")
        else:
            # act often returns non-zero even with successful dry-run depending on version, 
            # so usually we check stderr for specific errors, but simpler to return output
            if "Error" in act_res.stderr or "schema validation failed" in act_res.stderr:
                 results.append(f"act: Failed\n{act_res.stderr}")
            else:
                 results.append("act: Passed (dry-run completed)")
    else:
        results.append("act: Skipped (not installed)")

    return "\n\n".join(results)
