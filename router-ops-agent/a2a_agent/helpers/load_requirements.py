import logging
import os
import sys
from typing import Optional


logger = logging.getLogger(__name__)


def load_requirements(
    *,
    requirements_path: Optional[str] = None,
    exclude_list: list[str] = [],
) -> list[str]:
    """Loads requirements from the requirements.txt file.

    Args:
        requirements_path: Path to the requirements.txt file. If not 
        provided, uses "requirements.txt" as the default. If requirements.txt does not exist,
        returns an empty list.
        exclude_list: List of requirements to exclude from the returned list.

    Returns:
        List of requirements loaded from the file.
    """
    if not requirements_path:
        requirements_path = "requirements.txt"

    if not os.path.exists(requirements_path):
        logger.warning("Requirements file not found: %s", requirements_path)
        return []

    requirements_list = []
    with open(requirements_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line and not line.startswith("#"):
                requirements_list.append(line)

    return requirements_list
