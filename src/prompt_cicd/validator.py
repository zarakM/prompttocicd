"""Artifact validators for checking generated content."""

import yaml


class ValidationError(Exception):
    """Raised when artifact validation fails."""

    pass


class ArtifactValidator:
    """Validate generated CI/CD artifacts."""

    def validate_dockerfile(self, content: str) -> list[str]:
        """Validate Dockerfile syntax.

        Args:
            content: Dockerfile content to validate.

        Returns:
            List of warning/error messages (empty if valid).
        """
        issues = []
        lines = content.strip().split("\n")

        if not lines:
            issues.append("Dockerfile is empty")
            return issues

        # Check for FROM instruction
        has_from = any(
            line.strip().upper().startswith("FROM")
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        )
        if not has_from:
            issues.append("Dockerfile must have at least one FROM instruction")

        # Check for common issues
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Check if instructions are uppercase
            words = stripped.split()
            if words:
                instruction = words[0]
                known_instructions = {
                    "FROM",
                    "RUN",
                    "CMD",
                    "LABEL",
                    "EXPOSE",
                    "ENV",
                    "ADD",
                    "COPY",
                    "ENTRYPOINT",
                    "VOLUME",
                    "USER",
                    "WORKDIR",
                    "ARG",
                    "ONBUILD",
                    "STOPSIGNAL",
                    "HEALTHCHECK",
                    "SHELL",
                    "AS",
                }
                if instruction.upper() in known_instructions:
                    if instruction != instruction.upper():
                        issues.append(
                            f"Line {i}: Instruction '{instruction}' should be uppercase"
                        )

        return issues

    def validate_github_actions(self, content: str) -> list[str]:
        """Validate GitHub Actions workflow YAML.

        Args:
            content: GitHub Actions workflow content to validate.

        Returns:
            List of warning/error messages (empty if valid).
        """
        issues = []

        if not content.strip():
            issues.append("GitHub Actions workflow is empty")
            return issues

        try:
            workflow = yaml.safe_load(content)
        except yaml.YAMLError as e:
            issues.append(f"Invalid YAML: {e}")
            return issues

        if not isinstance(workflow, dict):
            issues.append("Workflow must be a YAML object")
            return issues

        # Check required fields
        if "name" not in workflow:
            issues.append("Workflow should have a 'name' field")

        if "on" not in workflow:
            issues.append("Workflow must have an 'on' trigger")

        if "jobs" not in workflow:
            issues.append("Workflow must have 'jobs'")
        elif not isinstance(workflow.get("jobs"), dict):
            issues.append("'jobs' must be an object")
        elif not workflow["jobs"]:
            issues.append("Workflow must have at least one job")

        return issues

    def validate_all(
        self, dockerfile_content: str | None = None, actions_content: str | None = None
    ) -> dict[str, list[str]]:
        """Validate all provided artifacts.

        Args:
            dockerfile_content: Optional Dockerfile content to validate.
            actions_content: Optional GitHub Actions content to validate.

        Returns:
            Dict mapping artifact name to list of issues.
        """
        results = {}

        if dockerfile_content is not None:
            results["Dockerfile"] = self.validate_dockerfile(dockerfile_content)

        if actions_content is not None:
            results["GitHub Actions"] = self.validate_github_actions(actions_content)

        return results
