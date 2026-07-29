import logging
import os
import pathlib
from typing import List, Optional
import yaml
from google.adk.skills import Skill, load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

logger = logging.getLogger("sysman-agent.helpers.get_skill_toolset")


def parse_frontmatter(skill_md_path: pathlib.Path) -> dict:
    """Parses YAML frontmatter block from a SKILL.md file.

    Args:
        skill_md_path: Path to the SKILL.md file.

    Returns:
        Dictionary of YAML frontmatter settings.
    """
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                try:
                    return yaml.safe_load(yaml_content) or {}
                except Exception:
                    # Fallback simple parser
                    data = {}
                    for line in yaml_content.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k = k.strip()
                            v = v.strip()
                            if v.startswith("[") and v.endswith("]"):
                                import json
                                try:
                                    v = json.loads(v)
                                except Exception:
                                    pass
                            data[k] = v
                    return data
    except Exception as err:
        logger.error(f"Error parsing frontmatter for {skill_md_path}: {err}")
    return {}


def get_skill_toolset(
    agent_type: str,
    categories: Optional[List[str]] = None,
) -> SkillToolset:
    """Discovers, filters, and loads modular skills from the common skill registry.

    Args:
        agent_type: The type of agent (e.g. 'Jira', 'Confluence', 'Linux').
        categories: The categories to filter by (e.g. ['SaaS', 'on-prem', 'Linux']).

    Returns:
        Configured SkillToolset.
    """
    env_skills_dir = os.getenv("SKILLS_DIR")
    if env_skills_dir:
        skills_dir = pathlib.Path(env_skills_dir)
    else:
        # Default relative to this helper: sysman-common/skills
        skills_dir = (
            pathlib.Path(__file__).parent.parent.parent.parent
            / "sysman-common"
            / "skills"
        )
        if not skills_dir.exists():
            # Try fallback inside app
            skills_dir = pathlib.Path(__file__).parent.parent / "skills"

    if not skills_dir.exists():
        logger.warning(f"Skills directory not found at {skills_dir.absolute()}")
        return SkillToolset(skills=[])

    skills: List[Skill] = []
    for skill_path in sorted(skills_dir.iterdir()):
        if not (skill_path.is_dir() and (skill_path / "SKILL.md").exists()):
            continue

        metadata = parse_frontmatter(skill_path / "SKILL.md")

        agent_types = metadata.get("agent_types", [])
        if not isinstance(agent_types, list):
            agent_types = [agent_types]

        skill_categories = metadata.get("categories", [])
        if not isinstance(skill_categories, list):
            skill_categories = [skill_categories]

        # Check Agent Type match
        type_match = agent_type in agent_types

        # Check Category match (if categories provided)
        category_match = True
        if categories:
            category_match = any(c in skill_categories for c in categories)

        if type_match and category_match:
            logger.info(
                f"Loading skill '{skill_path.name}' for agent type '{agent_type}'"
            )
            skills.append(load_skill_from_dir(skill_path))
        else:
            logger.debug(
                f"Skipping skill '{skill_path.name}' for agent type '{agent_type}'"
            )

    return SkillToolset(skills=skills)
