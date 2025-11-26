"""
Prompt loader for FUEL - inspired by KNighter's elegant prompt management.

This module provides a clean way to load and manage prompt templates from Markdown files.
"""

from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel


class Example(BaseModel):
    """Represents a single few-shot example."""

    code: str = ""
    analysis: str = ""
    apis: str = ""
    generated: str = ""
    coverage: str = ""
    exception: str = ""
    bug: str = ""

    @staticmethod
    def load_from_dir(example_dir: Path) -> "Example":
        """Load an example from a directory containing markdown files."""
        example = Example()

        # Try to load each component
        for field in ["code", "analysis", "apis", "generated", "coverage", "exception", "bug"]:
            file_path = example_dir / f"{field}.md"
            if file_path.exists():
                setattr(example, field, file_path.read_text().strip())

        return example


class PromptLoader:
    """
    Loads and manages prompt templates from Markdown files.

    Directory structure:
        prompts/
        ├── gen/
        │   ├── system.md
        │   ├── success.md
        │   ├── failure.md
        │   ├── default.md
        │   └── examples/
        │       ├── success_example1/
        │       │   ├── code.md
        │       │   ├── analysis.md
        │       │   ├── apis.md
        │       │   └── generated.md
        │       └── ...
        └── als/
            ├── system.md
            ├── success_coverage.md
            ├── failure_exception.md
            └── examples/
                └── ...
    """

    def __init__(self, prompt_dir: str = "prompts"):
        """Initialize the prompt loader.

        Args:
            prompt_dir: Root directory for prompts (default: "prompts")
        """
        self.prompt_dir = Path(prompt_dir)
        self.gen_dir = self.prompt_dir / "gen"
        self.als_dir = self.prompt_dir / "als"

        # Verify directories exist
        if not self.prompt_dir.exists():
            raise FileNotFoundError(
                f"Prompt directory not found: {self.prompt_dir.absolute()}"
            )

        logger.info(f"Prompt loader initialized from: {self.prompt_dir.absolute()}")

    def load_template(self, template_path: Path) -> str:
        """Load a single template file."""
        if not template_path.exists():
            logger.warning(f"Template file not found: {template_path}")
            return ""
        return template_path.read_text()

    def load_examples(
        self, examples_dir: Path, pattern: str = "*"
    ) -> List[Example]:
        """Load all examples from a directory.

        Args:
            examples_dir: Directory containing example subdirectories
            pattern: Pattern to filter example directories (e.g., "success_*")

        Returns:
            List of Example objects
        """
        examples = []

        if not examples_dir.exists():
            logger.warning(f"Examples directory not found: {examples_dir}")
            return examples

        # Find all matching example directories
        for example_dir in sorted(examples_dir.glob(pattern)):
            if example_dir.is_dir():
                try:
                    example = Example.load_from_dir(example_dir)
                    examples.append(example)
                    logger.debug(f"Loaded example from: {example_dir.name}")
                except Exception as e:
                    logger.warning(f"Failed to load example from {example_dir}: {e}")

        logger.info(f"Loaded {len(examples)} examples from {examples_dir.name}")
        return examples

    def format_examples(
        self,
        examples: List[Example],
        include_code: bool = True,
        include_analysis: bool = True,
        include_apis: bool = True,
        include_generated: bool = True,
        include_coverage: bool = False,
        include_exception: bool = False,
        include_bug: bool = False,
    ) -> str:
        """Format examples into a string for inclusion in prompts.

        Args:
            examples: List of Example objects
            include_*: Flags to control which components to include

        Returns:
            Formatted string containing all examples
        """
        if not examples:
            return ""

        formatted_parts = []

        for i, example in enumerate(examples, 1):
            parts = [f"## Example {i}\n"]

            if include_code and example.code:
                parts.append("### PyTorch Model\n")
                parts.append(example.code)
                parts.append("\n")

            if include_coverage and example.coverage:
                parts.append("### Coverage Result\n")
                parts.append(example.coverage)
                parts.append("\n")

            if include_exception and example.exception:
                parts.append("### Exception Message\n")
                parts.append(example.exception)
                parts.append("\n")

            if include_bug and example.bug:
                parts.append("### Bug Symptom\n")
                parts.append(example.bug)
                parts.append("\n")

            if include_analysis and example.analysis:
                parts.append(example.analysis)
                parts.append("\n")

            if include_apis and example.apis:
                parts.append("### Suggested APIs to use\n")
                parts.append(example.apis)
                parts.append("\n")

            if include_generated and example.generated:
                parts.append("### Generated Code\n")
                parts.append(example.generated)
                parts.append("\n")

            formatted_parts.append("".join(parts))

        return "\n---\n\n".join(formatted_parts)

    def load_gen_prompts(self) -> Dict[str, str]:
        """Load all generation prompts.

        Returns:
            Dictionary with keys: 'system', 'success', 'failure', 'default'
        """
        prompts = {}

        # Load system prompt
        prompts["system_content"] = self.load_template(self.gen_dir / "system.md")

        # Load success prompt with examples
        success_examples = self.load_examples(
            self.gen_dir / "examples", "success_*"
        )
        success_template = self.load_template(self.gen_dir / "success.md")
        prompts["success"] = success_template.replace(
            "{{examples}}",
            self.format_examples(
                success_examples,
                include_code=True,
                include_analysis=True,
                include_apis=True,
                include_generated=True,
            ),
        )

        # Load failure prompt with examples
        failure_examples = self.load_examples(
            self.gen_dir / "examples", "failure_*"
        )
        failure_template = self.load_template(self.gen_dir / "failure.md")
        prompts["failure"] = failure_template.replace(
            "{{examples}}",
            self.format_examples(
                failure_examples,
                include_code=True,
                include_analysis=True,
                include_apis=True,
                include_generated=True,
            ),
        )

        # Load default prompt with examples
        default_examples = self.load_examples(
            self.gen_dir / "examples", "default_*"
        )
        default_template = self.load_template(self.gen_dir / "default.md")
        prompts["default"] = default_template.replace(
            "{{examples}}",
            self.format_examples(
                default_examples,
                include_code=False,
                include_analysis=False,
                include_apis=True,
                include_generated=True,
            ),
        )

        logger.success("Successfully loaded all generation prompts")
        return prompts

    def load_als_prompts(self) -> Dict[str, Dict[str, str]]:
        """Load all analysis prompts.

        Returns:
            Nested dictionary with structure:
            {
                'system_content': str,
                'success': {
                    'coverage': str
                },
                'failure': {
                    'exception': str,
                    'bug': str
                }
            }
        """
        prompts = {}

        # Load system prompt
        prompts["system_content"] = self.load_template(self.als_dir / "system.md")

        # Load success coverage analysis prompt
        coverage_examples = self.load_examples(
            self.als_dir / "examples", "coverage_*"
        )
        coverage_template = self.load_template(self.als_dir / "success_coverage.md")
        prompts["success"] = {
            "coverage": coverage_template.replace(
                "{{examples}}",
                self.format_examples(
                    coverage_examples,
                    include_code=True,
                    include_coverage=True,
                    include_analysis=True,
                    include_apis=False,
                    include_generated=False,
                ),
            )
        }

        # Load failure exception analysis prompt (invalid test cases)
        exception_examples = self.load_examples(
            self.als_dir / "examples", "exception_*"
        )
        exception_template = self.load_template(self.als_dir / "failure_exception.md")
        
        # Load failure bug analysis prompt (oracle violations)
        bug_examples = self.load_examples(
            self.als_dir / "examples", "bug_*"
        )
        bug_template = self.load_template(self.als_dir / "failure_bug.md")
        
        prompts["failure"] = {
            "exception": exception_template.replace(
                "{{examples}}",
                self.format_examples(
                    exception_examples,
                    include_code=True,
                    include_exception=True,
                    include_analysis=True,
                    include_apis=False,
                    include_generated=False,
                ),
            ),
            "bug": bug_template.replace(
                "{{examples}}",
                self.format_examples(
                    bug_examples,
                    include_code=True,
                    include_bug=True,
                    include_analysis=True,
                    include_apis=False,
                    include_generated=False,
                ),
            )
        }

        logger.success("Successfully loaded all analysis prompts")
        return prompts


def load_prompts_from_markdown(
    prompt_dir: str = "prompts",
) -> tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    """Convenience function to load both generation and analysis prompts.

    Args:
        prompt_dir: Root directory for prompts

    Returns:
        Tuple of (gen_prompts, als_prompts)
    """
    loader = PromptLoader(prompt_dir)
    gen_prompts = loader.load_gen_prompts()
    als_prompts = loader.load_als_prompts()
    return gen_prompts, als_prompts

