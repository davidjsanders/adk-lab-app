import pathlib
from typing import List, Optional
from google.adk.skills import Skill, load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset


def get_skill_toolset(skill_names: Optional[List[str]] = None) -> SkillToolset:
    """Discovers and loads modular skills from the app/skills directory.

    Args:
        skill_names: Optional list of skill names to filter. If None, loads all.

    Returns:
        Configured SkillToolset.
    """
    skills_dir = pathlib.Path(__file__).parent.parent / "skills"
    if not skills_dir.exists():
        return SkillToolset(skills=[])

    skills: List[Skill] = []
    for skill_path in sorted(skills_dir.iterdir()):
        if not (skill_path.is_dir() and (skill_path / "SKILL.md").exists()):
            continue

        if skill_names is not None and skill_path.name not in skill_names:
            continue

        skills.append(load_skill_from_dir(skill_path))

    return SkillToolset(skills=skills)
