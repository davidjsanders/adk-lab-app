import logging
import os
import sys

logger = logging.getLogger(__name__)

def configure_paths() -> str:
    """Appends necessary workspace paths to Python path and resolves requirements file path.

    Returns:
        The absolute requirements.txt file path.
    """
    agent_engine_dir = os.path.dirname(os.path.abspath(__file__)) # a2a_samples/search/agent_engine
    search_dir = os.path.dirname(agent_engine_dir) # a2a_samples/search
    a2a_samples_dir = os.path.dirname(search_dir) # a2a_samples
    
    logger.debug("Configuring system paths. search_dir: %s", search_dir)
    if search_dir not in sys.path:
        sys.path.append(search_dir)
        logger.debug("Appended search_dir to sys.path: %s", search_dir)
        
    requirements_path = os.path.join(a2a_samples_dir, "requirements.txt")
    logger.info("Resolved requirements path: %s", requirements_path)
    return requirements_path

def load_environment() -> list[str]:
    """Loads settings from the agentengine.env configuration file into os.environ.

    Returns:
        List of environment variable keys loaded from the file.
    """
    # Sourced relative to the deploy script's directory (scripts/)
    search_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_dir = os.path.join(search_dir, "scripts")
    env_file = os.path.join(script_dir, "agentengine.env")
    env_vars_to_forward = []
    
    if os.path.exists(env_file):
        logger.info("Loading deployment environment from: %s", env_file)
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        key = key.strip()
                        os.environ[key] = value.strip('"').strip("'")
                        env_vars_to_forward.append(key)
                        logger.debug("Loaded env variable: %s -> %s", key, value)
                    except ValueError:
                        pass
    else:
        logger.warning("Environment file not found: %s", env_file)
        
    return env_vars_to_forward

def setup_gcloud() -> tuple[str, str, str]:
    """Retrieves and validates required Google Cloud credentials and configurations.

    Returns:
        A tuple containing (project, location, staging_bucket).

    Raises:
        ValueError: If any required GCP parameter is missing from environment.
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    staging_bucket = os.environ.get("GOOGLE_CLOUD_STAGING_BUCKET")
    
    logger.debug("Retrieving GCP configurations from environment...")
    if not project or not location or not staging_bucket:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, and GOOGLE_CLOUD_STAGING_BUCKET "
            "must be configured in agentengine.env."
        )
        
    logger.info("GCP Config: Project=%s, Location=%s, StagingBucket=%s", project, location, staging_bucket)
    return project, location, staging_bucket

def refine_environment(env_vars_to_forward: list[str]) -> dict[str, str]:
    """Assembles the final environment variables dictionary to forward to the reasoningEngine container.

    Args:
        env_vars_to_forward: Keys of the environment variables to forward.

    Returns:
        A dictionary of environment variables.
    """
    env = {}
    for key in env_vars_to_forward:
        if key in os.environ and os.environ[key] != "":
            if key in ("AGENT_ID", "REGION"):
                continue
            env[key] = os.environ[key]

    if os.environ.get("VERSION"):
        env["VERSION"] = os.environ.get("VERSION")

    if "LOG_LEVEL" not in env:
        env["LOG_LEVEL"] = "DEBUG"
        
    logger.info("Refined environment keys to forward: %s", list(env.keys()))
    return env
