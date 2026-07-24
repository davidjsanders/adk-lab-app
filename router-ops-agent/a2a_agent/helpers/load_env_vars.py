import logging
import os
import sys
from dotenv import dotenv_values
from typing import Any, Optional

logger = logging.getLogger(__name__)


def load_env_vars(
    *,
    env_file: Optional[str] = None,
    exclude_list: list[str] = [],
) -> dict[str, Any]:
    """Loads settings from a given env configuration file into 
    a dictionary.

    Args:
        env_file: Path to the environment configuration file. If not 
        provided, uses ".env" as the default. If .env does not exist,
        returns an empty dict.

    Returns:
        Dictionary of environment variable names and values loaded from 
        the file.
    """
    if not env_file:
        env_file = ".env"

    if not os.path.exists(env_file):
        logger.warning("Environment file not found: %s", env_file)
        return {}

    logger.info("Loading environment from: %s", env_file)
    env_vars = dict(dotenv_values(env_file))
    
    for key in exclude_list:
        env_vars.pop(key, None)

    return env_vars
