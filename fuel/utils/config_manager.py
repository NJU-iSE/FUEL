"""
Configuration management utilities for FUEL.

This module handles automatic detection, downloading, and creation of configuration files.
"""

import os

import requests
from loguru import logger

# Default configuration file URLs for download
DEFAULT_CONFIG_URLS = {
    "model.yaml": "https://raw.githubusercontent.com/shaoyuyoung/fuel_config_data/main/config/model.yaml",
    "heuristic.yaml": "https://raw.githubusercontent.com/shaoyuyoung/fuel_config_data/main/config/heuristic.yaml",
    "gen_prompt": "https://raw.githubusercontent.com/shaoyuyoung/fuel_config_data/main/config/gen_prompt/",
    "als_prompt": "https://raw.githubusercontent.com/shaoyuyoung/fuel_config_data/main/config/als_prompt/",
}


def ensure_config_file_exists(
    config_path: str, config_type: str, lib: str = None
) -> str:
    """
    Ensure configuration file exists, download if necessary.

    Args:
        config_path: Path to the config file
        config_type: Type of config ('model', 'heuristic', 'gen_prompt', 'als_prompt')
        lib: Library name for prompt configs

    Returns:
        Valid path to the configuration file
    """
    if config_path is None:
        logger.warning(f"Config path for {config_type} is None, using default")
        # Set default paths
        if config_type == "model":
            config_path = "config/model.yaml"
        elif config_type == "heuristic":
            config_path = "config/heuristic.yaml"
        elif config_type == "gen_prompt":
            config_path = "config/gen_prompt"
        elif config_type == "als_prompt":
            config_path = "config/als_prompt"

    # For prompt configs, check both directory and specific file
    if config_type in ["gen_prompt", "als_prompt"] and lib:
        # First check if the directory exists
        if not os.path.exists(config_path):
            logger.warning(
                f"Config directory {config_path} does not exist, creating..."
            )
            os.makedirs(config_path, exist_ok=True)

        # Then check the specific library file
        full_config_path = os.path.join(config_path, f"{lib}.yaml")
        if not os.path.exists(full_config_path):
            logger.warning(
                f"Config file {full_config_path} does not exist, attempting to download..."
            )
            _download_config_file(config_type, full_config_path, lib)
    else:
        # For single config files
        if not os.path.exists(config_path):
            logger.warning(
                f"Config file {config_path} does not exist, attempting to download..."
            )
            _download_config_file(config_type, config_path)

    return config_path


def _download_config_file(config_type: str, save_path: str, lib: str = None):
    """Download configuration file from remote URL or create default"""
    url = ""  # Initialize url to ensure it's always defined
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Construct download URL
        if config_type in ["gen_prompt", "als_prompt"] and lib:
            url = DEFAULT_CONFIG_URLS[config_type] + f"{lib}.yaml"
        elif config_type in ["model", "heuristic"]:
            url = DEFAULT_CONFIG_URLS[f"{config_type}.yaml"]
        else:
            raise ValueError(f"Unknown config type: {config_type}")

        logger.info(f"Downloading {config_type} config from {url}")

        # Try to download
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes

        with open(save_path, "wb") as f:
            f.write(response.content)

        logger.success(f"Successfully downloaded {config_type} config to {save_path}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download config file from {url}: {e}")
        raise ConnectionError(
            f"Network error: Failed to download configuration file from {url}. Please check your network connection and the URL."
        ) from e
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while trying to download config file from {url}: {e}"
        )
        # Re-raise the original exception or a more specific one if appropriate
        # For now, we'll wrap it in a generic RuntimeError to indicate failure in this part of the code.
        raise RuntimeError(
            f"Failed to process or download configuration file from {url} due to an unexpected error."
        ) from e


def validate_all_configs(
    lib: str, gen_prompt_config: str, als_prompt_config: str, heuristic_config: str
) -> dict:
    """
    Validate and ensure all configuration files exist.

    Args:
        lib: Library name
        gen_prompt_config: Path to gen prompt config
        als_prompt_config: Path to als prompt config
        heuristic_config: Path to heuristic config

    Returns:
        Dictionary with validated config paths
    """
    try:
        validated_configs = {}

        # Validate gen prompt config
        gen_prompt_base = ensure_config_file_exists(
            gen_prompt_config, "gen_prompt", lib
        )
        validated_configs["GEN_PROMPT_CONFIG"] = gen_prompt_base + f"/{lib}.yaml"

        # Validate als prompt config
        als_prompt_base = ensure_config_file_exists(
            als_prompt_config, "als_prompt", lib
        )
        validated_configs["ALS_PROMPT_CONFIG"] = als_prompt_base + f"/{lib}.yaml"

        # Validate heuristic config
        validated_configs["HEURISTIC_CONFIG"] = ensure_config_file_exists(
            heuristic_config, "heuristic"
        )

        logger.success("All configuration files validated successfully")
        return validated_configs

    except Exception as e:
        logger.error(f"Failed to setup configuration files: {e}")
        raise ValueError(f"Configuration setup failed: {e}")
