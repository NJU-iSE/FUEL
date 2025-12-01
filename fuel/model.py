import os
import time
from abc import abstractmethod
from pathlib import Path

import yaml
from loguru import logger
from openai import OpenAI

try:
    os.environ["VLLM_USE_V1"] = "1"
    from vllm import LLM, SamplingParams
except ImportError:
    logger.warning(
        "currently, vllm still can't be install with nightly pytorch, refer to https://github.com/vllm-project/vllm/issues/9180"
    )

from transformers import (
    AutoTokenizer,
)

os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"


class Model:
    """
    a classes for managing the LLM model (server and local)
    """

    def __init__(self, config, **kwargs):
        self.config = config

    @abstractmethod
    def generate(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def analyze(self, **kwargs):
        raise NotImplementedError


class RemoteModel(Model):
    """
    managing remote LLM model (gen and als)
    """

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)

        self.config = config
        # Add timeout setting support
        timeout = self.config.get("timeout", 30)  # Default 30 seconds timeout

        self.client = OpenAI(
            api_key=Path(self.config["key_file"]).read_text().strip(),
            base_url=self.config["url"],
            timeout=timeout,
        )

        # Verify connection and network configuration
        self._verify_connection()

    def _verify_connection(self):
        """Verify network connection and API configuration"""
        import requests

        try:
            # Check basic network connection
            logger.info("Checking network connection...")
            requests.get(self.config["url"].replace("/beta", ""), timeout=10)
            logger.success("Network connection is working")

            # Check proxy settings
            proxy_info = []
            for proxy_var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                if os.environ.get(proxy_var):
                    proxy_info.append(f"{proxy_var}={os.environ.get(proxy_var)}")

            if proxy_info:
                logger.info(f"Detected proxy settings: {', '.join(proxy_info)}")
            else:
                logger.info("No proxy settings detected")

        except Exception as e:
            logger.warning(f"Network check failed: {e}")
            logger.warning("Please check your network connection and proxy settings")

    def generate(self, **kwargs):
        raise NotImplementedError

    def analyze(self, **kwargs):
        raise NotImplementedError

    def get_outputs(self, role, prompt, code_gen):
        messages = [
            {"role": "system", "content": role},
            {"role": "user", "content": f"{prompt}"},
        ]

        # @SHAOYU: Different LLM API service providers have different machenism to be forced to generate code.
        # We use different processing ways for different providers.
        if code_gen:
            if "deepseek" in self.config["model"]:
                messages.append(
                    {"role": "assistant", "content": "```python\n", "prefix": True}
                )
            elif "kimi" in self.config["model"]:
                messages.append(
                    {"role": "assistant", "content": "```python\n", "partial": True}
                )
            else:
                raise NotImplementedError(
                    f"Unsupported RemoteModel: {self.config['model']}"
                )

        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                stop=["```"] if code_gen else None,
            )

            gen_text = response.choices[0].message.content
            return gen_text
        except Exception as e:
            logger.warning(f"API call failed: {type(e).__name__}: {str(e)}")
            # Wait before retry
            time.sleep(2)
            return None


class LocalModel(Model):
    """
    managing local LLM model (gen and als) using vllm
    """

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
        self.config = config
        self.model_name = self.config["model"]
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.native_model = LLM(
            model=self.config["model"],
            dtype=self.config["dtype"],
            tensor_parallel_size=self.config["gpu_numbers"],
            swap_space=self.config["swap_space"],
            **kwargs,
        )
        self.sampling_params = SamplingParams(
            n=self.config["num"],
            temperature=self.config["temperature"],
            top_p=self.config["top_p"],
            repetition_penalty=self.config["repetition_penalty"],
            max_tokens=self.config["max_tokens"],
            stop=self.config["stop"],
        )

    def generate(self, **kwargs):
        raise NotImplementedError

    def analyze(self, **kwargs):
        raise NotImplementedError


class AlsRemoteModel(RemoteModel):
    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)

    def analyze(self, role, prompt, **kwargs):
        retry_times = self.config["retry_times"]
        cnt = 0
        base_delay = 5  # Base delay time (seconds)

        while cnt < retry_times:
            logger.info(
                f"Attempting analyze API call (attempt {cnt + 1}/{retry_times})"
            )

            gen_text = self.get_outputs(role, prompt, False)
            if gen_text is not None:
                logger.success(f"API call succeeded (attempt {cnt + 1})")
                return gen_text
            else:
                cnt += 1
                if cnt < retry_times:
                    # Exponential backoff: double delay time for each retry
                    delay = base_delay * (2 ** (cnt - 1))
                    logger.warning(f"API call failed, retrying in {delay} seconds...")
                    time.sleep(delay)

        logger.error(f"API service failed after {retry_times} retries")
        raise Exception(
            f"API service is down after {retry_times} times of retry when analyzing"
        )


class GenRemoteModel(RemoteModel):
    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)

    def generate(self, role, prompt, **kwargs):
        retry_times = self.config["retry_times"]
        cnt = 0
        base_delay = 5  # Base delay time (seconds)

        while cnt < retry_times:
            logger.info(
                f"Attempting generate API call (attempt {cnt + 1}/{retry_times})"
            )

            gen_text = self.get_outputs(role, prompt, True)
            if gen_text is not None:
                logger.success(f"API call succeeded (attempt {cnt + 1})")
                return gen_text
            else:
                cnt += 1
                if cnt < retry_times:
                    # Exponential backoff: double delay time for each retry
                    delay = base_delay * (2 ** (cnt - 1))
                    logger.warning(f"API call failed, retrying in {delay} seconds...")
                    time.sleep(delay)

        logger.error(f"API service failed after {retry_times} retries")
        raise Exception(
            f"API service is down after {retry_times} times of retry when generating"
        )


class GenLocalModel(LocalModel):
    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)

    def generate(self, role, prompt, **kwargs):
        messages = [
            {"role": "system", "content": role},
            {"role": "user", "content": f"{prompt}"},
        ]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        outputs = self.native_model.generate([text], self.sampling_params)

        return outputs[0].outputs[0].text


class AlsLocalModel(LocalModel):  # TODO@SHAOYU: add the analyze function for als model
    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)

    def analyze(
        self, prompt_config, res_dir, flag: bool, feedback: dict = None, **kwargs
    ):
        raise NotImplementedError


def load_model_from_config(config_path):
    """
    Load model instances from configuration file

    Args:
        config_path: Path to configuration file

    Returns:
        tuple: (gen_model, als_model) corresponding model instances
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    method = config.get("method", "remote")
    model_config = config.get("config", {})

    if method == "local":
        gen_model = GenLocalModel(model_config)
        als_model = AlsLocalModel(model_config)
        logger.info(f"[LOCAL] Loaded model: {model_config.get('model', 'Unknown')}")
    elif method == "remote":
        gen_model = GenRemoteModel(model_config)
        als_model = AlsRemoteModel(model_config)
        logger.info(f"[REMOTE] Loaded model: {model_config.get('model', 'Unknown')}")
    else:
        raise ValueError(f"Unsupported model method: {method}")

    return gen_model, als_model


def load_single_model_from_config(config_path, model_type):
    """
    Load single model instance from configuration file

    Args:
        config_path: Path to configuration file
        model_type: Model type ('gen' or 'als')

    Returns:
        Model instance
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    method = config.get("method", "remote")
    model_config = config.get("config", {})

    if method == "local":
        if model_type == "gen":
            model = GenLocalModel(model_config)
        elif model_type == "als":
            model = AlsLocalModel(model_config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        logger.info(
            f"[LOCAL] Loaded {model_type} model: {model_config.get('model', 'Unknown')}"
        )
    elif method == "remote":
        if model_type == "gen":
            model = GenRemoteModel(model_config)
        elif model_type == "als":
            model = AlsRemoteModel(model_config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        logger.info(
            f"[REMOTE] Loaded {model_type} model: {model_config.get('model', 'Unknown')}"
        )
    else:
        raise ValueError(f"Unsupported model method: {method}")

    return model
