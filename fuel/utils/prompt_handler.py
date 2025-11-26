import re
from pathlib import Path
from typing import Dict, Tuple

from loguru import logger

from ..feedback.feedback import FeedBack
from .prompt_loader import load_prompts_from_markdown


def load_prompts(prompt_dir: str = "prompts") -> Tuple[Dict, Dict]:
    """Load prompts from Markdown format.

    Args:
        prompt_dir: Path to prompts directory (default: "prompts")

    Returns:
        Tuple of (gen_prompt_config, als_prompt_config)

    Raises:
        FileNotFoundError: If prompts directory doesn't exist

    Examples:
        >>> gen_prompts, als_prompts = load_prompts("prompts")
    """
    prompt_path = Path(prompt_dir)

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompts directory not found: {prompt_path.absolute()}\n"
            f"Please ensure the 'prompts/' directory exists with Markdown templates."
        )

    if not prompt_path.is_dir():
        raise ValueError(
            f"Expected directory, got file: {prompt_path}\n"
            f"Please provide the path to the prompts directory."
        )

    logger.info(f"Loading prompts from Markdown: {prompt_path.absolute()}")

    try:
        gen_prompts, als_prompts = load_prompts_from_markdown(str(prompt_path))
        logger.success(
            f"✓ Successfully loaded prompts: {len(gen_prompts)} gen types, {len(als_prompts)} als types"
        )
        return gen_prompts, als_prompts
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        raise RuntimeError(f"Error loading Markdown prompts from {prompt_path}: {e}")


class PromptHandler:
    """Utility class for handling generation and analysis prompts."""

    def __init__(self, gen_prompt_config, als_prompt_config):
        """Initialize prompt handler.
        
        Args:
            gen_prompt_config: Dictionary containing generation prompt templates
            als_prompt_config: Dictionary containing analysis prompt templates
        """
        self.gen_prompt_config = gen_prompt_config
        self.als_prompt_config = als_prompt_config

    def get_prompts(self, feedback_data, lib, op_nums, heuristic=None):
        """Generate appropriate prompts based on current state"""
        statue = feedback_data.get("statue", True)
        _feedback = feedback_data.get("feedback", {})

        # Determine whether to use default prompt
        if (
            (FeedBack.success_times < 2 and statue)
            or FeedBack.cons_fail > 2
            or FeedBack.fix_failed
        ):
            FeedBack.cons_fail = 0
            gen_prompt = self.gen_prompt_config["default"]
            als_text = "use generation by default"
            return gen_prompt, als_text

        # Select prompts based on success/failure status
        if statue:
            als_prompt = self.als_prompt_config["success"]["coverage"]
            als_prompt = re.sub(r"\{coverage}", _feedback["coverage"], als_prompt)
            gen_prompt = self.gen_prompt_config["success"]
        else:
            FeedBack.cons_fail += 1
            try:
                als_prompt = self.als_prompt_config["failure"]["exception"]
            except KeyError:
                als_prompt = self.als_prompt_config["failure"]
            als_prompt = re.sub(r"\{exception}", _feedback["exception"], als_prompt)
            gen_prompt = self.gen_prompt_config["failure"]

        # Process common prompt replacements
        als_prompt = re.sub(r"\{code}", _feedback["code"], als_prompt)
        gen_prompt = re.sub(r"\{code}", _feedback["code"], gen_prompt)

        return gen_prompt, als_prompt

    def process_generation_prompt(self, gen_prompt, als_text, op_nums, heuristic=None):
        """Process final replacements for generation prompt"""
        gen_prompt = re.sub(
            r"\{als_res}", re.escape(als_text).replace("\\", ""), gen_prompt
        )
        gen_prompt = re.sub(r"\{op_nums}", str(op_nums), gen_prompt)

        # Process heuristic algorithm related replacements
        if heuristic != "None" and heuristic is not None:
            if FeedBack.new_ops == []:
                new_ops = heuristic.get_ops()
                FeedBack.cur_ops = new_ops
                FeedBack.delta_lines = 0
            gen_prompt = re.sub(r"\{new_ops}", "\n".join(FeedBack.cur_ops), gen_prompt)
            logger.info(f"current op(s) is/are {FeedBack.cur_ops}")

        return gen_prompt
