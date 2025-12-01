import os

import click
from loguru import logger

from .feedback.execution_status import ExecutionStatus
from .feedback.feedback import FeedBack
from .utils.Filer import File
from .utils.fuzzing_core import FuzzingCore
from .utils.model_manager import ModelManager
from .utils.prompt_handler import PromptHandler, load_prompts

ROOT_DIR = os.getcwd()


@click.group()
@click.option(
    "lib",
    "--lib",
    type=str,
    default="pytorch",
    help="Library Under Test",
)
@click.option(
    "gen_model_config",
    "--gen_model_config",
    type=str,
    default="model_config/deepseek.yaml",
    help="Path to the generation model configuration file",
)
@click.option(
    "als_model_config",
    "--als_model_config",
    type=str,
    default="model_config/deepseek.yaml",
    help="Path to the analysis model configuration file",
)
@click.option(
    "heuristic_config",
    "--heuristic_config",
    type=str,
    default="model_config/heuristic.yaml",
    help="Path to the heuristic configuration file",
)
@click.option(
    "prompt_dir",
    "--prompt_dir",
    type=str,
    default="prompts",
    help="Path to the prompts directory (Markdown format)",
)
@click.option(
    "log_level",
    "--log_level",
    type=click.Choice(
        ["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=False,
    ),
    default="INFO",
    help="Log level (default: INFO). Set to INFO to hide DEBUG messages.",
)
@click.pass_context
def cli(
    ctx,
    lib,
    gen_model_config,
    als_model_config,
    heuristic_config,
    prompt_dir,
    log_level,
):
    # Configure logger level
    logger.remove()  # Remove default handler
    logger.add(
        lambda msg: print(msg, end=""),  # Print to stdout
        level=log_level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
    )

    ctx.ensure_object(dict)
    ctx.obj["lib"] = lib
    ctx.obj["GEN_MODEL_CONFIG"] = gen_model_config
    ctx.obj["ALS_MODEL_CONFIG"] = als_model_config
    ctx.obj["HEURISTIC_CONFIG"] = heuristic_config
    ctx.obj["PROMPT_DIR"] = prompt_dir


@cli.command("run_fuzz")
@click.pass_context
@click.option(
    "res_dir",
    "--res_dir",
    type=str,
    default="results/fuel",
    help="dir consisting generated programs",
)
@click.option(
    "output_dir",
    "--output_dir",
    type=str,
    default="output",
    help="dir consisting log and coverage file",
)
@click.option(
    "diff_type",
    "--diff_type",
    type=str,
    default="cpu_compiler",
    help="differential testing types including: `hardware`, `cpu_compiler`, `cuda_compiler`",
)
@click.option(
    "max_round", "--max_round", type=int, default=1000, help="max round of fuzzing"
)
@click.option(
    "max_time", "--max_time", type=int, default=10000, help="max time for fuzzing"
)
@click.option(
    "heuristic",
    "--heuristic",
    type=str,
    default="FASA",
    help="use some heuristic to generate tests",
)
@click.option(
    "op_set",
    "--op_set",
    type=str,
    default=lambda: f"data/{click.get_current_context().parent.params['lib']}_operators.txt",
    help="source dataset of heuristic search",
)
@click.option(
    "op_nums",
    "--op_nums",
    type=int,
    default=5,
    help="number of operators to generate (note that this is a extra limitation in prompts for LLMs)",
)
def run_fuzz(
    ctx,
    res_dir,
    output_dir,
    diff_type,
    max_round,
    max_time,
    heuristic,
    op_set,
    op_nums,
):
    """Execute fuzzing test"""
    lib = ctx.obj["lib"]

    # Load prompts from Markdown format
    # TODO: Support ablation studies (wo_heuristic) by using different prompt directories
    try:
        gen_prompt_config, als_prompt_config = load_prompts(ctx.obj["PROMPT_DIR"])
    except FileNotFoundError as e:
        logger.error(str(e))
        raise click.ClickException(
            f"Prompts directory not found: {ctx.obj['PROMPT_DIR']}. "
            "Please ensure the prompts directory exists with Markdown templates."
        )

    # Setup models
    gen_model, als_model = ModelManager.setup_models(
        gen_model_config=ctx.obj["GEN_MODEL_CONFIG"],
        als_model_config=ctx.obj["ALS_MODEL_CONFIG"],
    )

    # Setup heuristic algorithm
    heuristic_instance = ModelManager.setup_heuristic(
        heuristic, ctx.obj["HEURISTIC_CONFIG"], op_set
    )

    # Initialize components
    diff_type = diff_type.replace("\n", "").replace(" ", "").replace("\r", "")
    FeedBack.init(lib, diff_type)
    File.init(ROOT_DIR, res_dir, output_dir, lib)

    # Create utility class instances
    prompt_handler = PromptHandler(gen_prompt_config, als_prompt_config)
    fuzzing_core = FuzzingCore(gen_model, als_model, prompt_handler, lib)

    # Initialize variables
    feedback_data = {"status": ExecutionStatus.SUCCESS, "feedback": {}}
    flag = True  # Fix flag

    # Start fuzzing
    logger.success("fuzzing starts!\n")

    while FeedBack.cur_round < max_round:
        # Execute single round test
        file_path = fuzzing_core.execute_single_round(
            feedback_data, heuristic_instance, op_nums, diff_type
        )

        # Handle execution results
        flag = fuzzing_core.handle_execution_results(file_path, flag)

        # Process feedback
        feedback_data = fuzzing_core.process_feedback(file_path)

        # Increment round
        FeedBack.cur_round += 1


if __name__ == "__main__":
    cli()
