import os

from loguru import logger

from ..guidance.FASA import FASA
from ..guidance.Random import Random
from ..model import (
    load_single_model_from_config,
)
from .util import load_config_file


class ModelManager:
    """Utility class for managing models and heuristic algorithms"""

    @staticmethod
    def setup_models(
        gen_model_config=None,
        als_model_config=None,
        gen_model_path=None,
        als_model_path=None,
    ):
        """
        Setup generation and analysis models from configuration files

        Args:
            gen_model_config: Path to generation model configuration file
            als_model_config: Path to analysis model configuration file
            gen_model_path: Path to generation model configuration file (alias)
            als_model_path: Path to analysis model configuration file (alias)

        Returns:
            tuple: (gen_model, als_model)
        """
        # Support different parameter names
        gen_config_path = gen_model_config or gen_model_path
        als_config_path = als_model_config or als_model_path

        if not gen_config_path or not als_config_path:
            raise ValueError(
                "Must provide configuration file paths for both generation and analysis models"
            )

        # Check if configuration files exist
        if not os.path.exists(gen_config_path):
            raise FileNotFoundError(
                f"Generation model configuration file not found: {gen_config_path}"
            )
        if not os.path.exists(als_config_path):
            raise FileNotFoundError(
                f"Analysis model configuration file not found: {als_config_path}"
            )

        # Load models
        gen_model = load_single_model_from_config(gen_config_path, "gen")
        als_model = load_single_model_from_config(als_config_path, "als")

        return gen_model, als_model

    @staticmethod
    def get_available_models(model_dir="config/model"):
        """
        Get list of available model configuration files

        Args:
            model_dir: Model configuration directory

        Returns:
            list: List of available model configuration files
        """
        if not os.path.exists(model_dir):
            return []

        model_files = []
        for file in os.listdir(model_dir):
            if file.endswith(".yaml") or file.endswith(".yml"):
                model_files.append(file)

        return sorted(model_files)

    @staticmethod
    def setup_heuristic(heuristic_name, heuristic_config_path, op_set):
        """Setup heuristic algorithm"""
        heuristic_name = heuristic_name.replace("\r", "")

        if heuristic_name == "None":
            logger.info("[HEURISTIC]: None!")
            return None

        heuristic_config = load_config_file(heuristic_config_path)[heuristic_name]

        if heuristic_name == "FASA":
            logger.info("[HEURISTIC]: Feedback-Aware Simulated Annealing!")
            return FASA(
                float(heuristic_config["t0"]),
                float(heuristic_config["tmin"]),
                float(heuristic_config["alpha"]),
                op_set,
            )
        elif heuristic_name == "Random":
            logger.info("[HEURISTIC]: Random!")
            return Random(
                int(heuristic_config["l"]), int(heuristic_config["r"]), op_set
            )

        return None
