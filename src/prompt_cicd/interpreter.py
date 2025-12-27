"""Intent interpreter for parsing natural language prompts into structured DevOps intent."""

import json
import os
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field


class DevOpsIntent(BaseModel):
    """Structured representation of DevOps pipeline requirements."""

    language: str = Field(description="Programming language (e.g., nodejs, python, go)")
    runtime: str = Field(description="Runtime environment (e.g., node, python, go)")
    runtime_version: str = Field(
        default="20", description="Runtime version (e.g., 20, 3.11, 1.21)"
    )
    build_tool: Optional[str] = Field(
        default=None, description="Build tool (e.g., npm, yarn, pip, go)"
    )
    build_command: Optional[str] = Field(
        default=None, description="Build command (e.g., npm run build)"
    )
    test_command: Optional[str] = Field(
        default=None, description="Test command (e.g., npm test)"
    )
    expose_port: Optional[int] = Field(
        default=None, description="Port to expose (e.g., 3000, 8080)"
    )
    package_manager_lock_file: Optional[str] = Field(
        default=None,
        description="Lock file name (e.g., package-lock.json, yarn.lock, requirements.txt)",
    )
    ci_provider: str = Field(
        default="github-actions",
        description="CI provider (e.g., github-actions, gitlab-ci)",
    )
    start_command: Optional[str] = Field(
        default=None, description="Command to start the application"
    )


SYSTEM_PROMPT = """You are a DevOps expert. Parse the user's natural language description of their application and CI/CD requirements into a structured JSON format.

Extract the following information:
- language: The programming language (nodejs, python, go, java, etc.)
- runtime: The runtime environment (node, python, go, java, etc.)
- runtime_version: The version of the runtime (e.g., "20" for Node 20, "3.11" for Python 3.11)
- build_tool: The package manager or build tool (npm, yarn, pip, poetry, go, maven, etc.)
- build_command: The command to build the project (e.g., "npm run build")
- test_command: The command to run tests (e.g., "npm test")
- expose_port: The port the application listens on (e.g., 3000, 8080)
- package_manager_lock_file: The lock file name (e.g., "package-lock.json", "yarn.lock")
- ci_provider: The CI/CD provider (default: "github-actions")
- start_command: The command to start the application (e.g., "npm start", "node server.js")

Use sensible defaults based on the language/runtime if not explicitly specified:
- Node.js: npm, package-lock.json, port 3000, "npm start"
- Python: pip, requirements.txt, port 8000, "python app.py"
- Go: go, go.sum, port 8080, "./app"

Return ONLY valid JSON matching the schema, no explanation."""


class IntentInterpreter:
    """Interprets natural language prompts into structured DevOps intent."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the interpreter with OpenAI client.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def interpret(self, prompt: str) -> DevOpsIntent:
        """Parse a natural language prompt into structured DevOps intent.

        Args:
            prompt: Natural language description of the application and CI/CD needs.

        Returns:
            DevOpsIntent with extracted information.

        Raises:
            ValueError: If the prompt cannot be parsed.
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")

        try:
            data = json.loads(content)
            return DevOpsIntent(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to create DevOpsIntent: {e}") from e
