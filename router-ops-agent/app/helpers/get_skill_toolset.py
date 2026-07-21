# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper function for creating an ADK SkillToolset scoped to specific agent skills."""

import pathlib
from google.adk.skills import Skill, load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset


def get_skill_toolset(skill_names: list[str] | None = None) -> SkillToolset:
    """Discovers and loads modular skills from the app/skills directory.

    Args:
        skill_names: Optional list of skill directory names (e.g. ['router-fleet']) to filter and load. If None, loads all discovered skills.

    Returns:
        A configured SkillToolset ready to be passed to Agent(tools=[...]).

    Raises:
        None.
    """
    skills_dir = pathlib.Path(__file__).parent.parent / "skills"
    if not skills_dir.exists():
        return SkillToolset(skills=[])

    skills: list[Skill] = []
    for skill_path in sorted(skills_dir.iterdir()):
        if not (skill_path.is_dir() and (skill_path / "SKILL.md").exists()):
            continue

        if skill_names is not None and skill_path.name not in skill_names:
            continue

        skills.append(load_skill_from_dir(skill_path))

    return SkillToolset(skills=skills)
