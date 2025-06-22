import os

import click
from loguru import logger

from .feedback.feedback import FeedBack
from .utils.Filer import File
from .utils.util import load_config_file
from .utils.config_manager import validate_all_configs
from .utils.model_manager import ModelManager
from .utils.prompt_handler import PromptHandler
from .utils.fuzzing_core import FuzzingCore

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
    "model_config",
    "--model_config",
    type=str,
    default="config/model.yaml",
    help="Path to the model configuration file",
)
@click.option(
    "gen_prompt_config",
    "--gen_prompt_config",
    type=str,
    default="config/gen_prompt",
    help="Path to the prompt configuration file",
)
@click.option(
    "als_prompt_config",
    "--als_prompt_config",
    type=str,
    default="config/als_prompt",
    help="Path to the prompt configuration file",
)
@click.option(
    "heuristic_config",
    "--heuristic_config",
    type=str,
    default="config/heuristic.yaml",
    help="Path to the heuristic configuration file",
)
@click.pass_context
def cli(ctx, lib, model_config, gen_prompt_config, als_prompt_config, heuristic_config):
    ctx.ensure_object(dict)
    ctx.obj["lib"] = lib

    # Validate and ensure all config files exist
    try:
        validated_configs = validate_all_configs(
            lib=lib,
            model_config=model_config,
            gen_prompt_config=gen_prompt_config,
            als_prompt_config=als_prompt_config,
            heuristic_config=heuristic_config
        )
        
        # Store validated config paths
        ctx.obj.update(validated_configs)
        
    except Exception as e:
        logger.error(f"Failed to setup configuration files: {e}")
        raise click.ClickException(f"Configuration setup failed: {e}")


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
    "use_local_gen",
    "--use_local_gen",
    is_flag=True,
    default=False,
    help="whether to use local model to generate tests",
)
@click.option(
    "heuristic",
    "--heuristic",
    type=str,
    default="SA",
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
    use_local_gen,
    heuristic,
    op_set,
    op_nums,
):
    """Execute fuzzing test"""
    lib = ctx.obj["lib"]
    
    # Load configuration files
    model_config, gen_prompt_config, als_prompt_config = (
        load_config_file(ctx.obj["MODEL_CONFIG"]),
        load_config_file(
            ctx.obj["GEN_PROMPT_CONFIG"]
            if heuristic != "None"
            else ctx.obj["GEN_PROMPT_CONFIG"].replace("/", "/ablations/wo_heuristic/", 1)
        ),
        load_config_file(ctx.obj["ALS_PROMPT_CONFIG"]),
    )

    # Setup models
    gen_model, als_model = ModelManager.setup_models(model_config, use_local_gen)
    
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
    feedback_data = {"statue": True, "feedback": {}}
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
