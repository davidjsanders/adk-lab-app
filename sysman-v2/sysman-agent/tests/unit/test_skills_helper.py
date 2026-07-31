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

"""Unit tests for SkillsHelper."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.classes.skills_helper import SkillsHelper
from app.models.registry_resource_type import RegistryResourceType
from app.models.settings import Settings


@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.google_cloud_project = "test-project"
    settings.google_cloud_location = "us-central1"
    return settings


def setup_mock_registry(mock_registry, get_skill_async_return=None, get_skill_async_side_effect=None):
    mock_registry._run_async.side_effect = lambda coro: asyncio.run(coro)
    if get_skill_async_side_effect:
        mock_registry.get_skill_async = AsyncMock(side_effect=get_skill_async_side_effect)
    else:
        mock_registry.get_skill_async = AsyncMock(return_value=get_skill_async_return)


@patch("app.classes.skills_helper.RegistryHelper")
def test_skills_helper_get_skills_empty(mock_registry_helper_cls, mock_settings) -> None:
    """Verifies that get_skills returns an empty list if no skills are provided."""
    helper = SkillsHelper(settings=mock_settings, skills=[])
    assert helper.get_skills() == []


@patch("app.classes.skills_helper.RegistryHelper")
def test_skills_helper_get_skills_success(mock_registry_helper_cls, mock_settings) -> None:
    """Verifies that get_skills correctly resolves a skill display name to a Skill object."""
    mock_registry = mock_registry_helper_cls.return_value
    mock_registry.find.return_value = [{"name": "projects/test-project/locations/us-central1/skills/my-skill"}]

    mock_skill_obj = MagicMock()
    setup_mock_registry(mock_registry, get_skill_async_return=mock_skill_obj)

    helper = SkillsHelper(settings=mock_settings, skills=["my-skill"])
    resolved = helper.get_skills()

    assert resolved == [mock_skill_obj]
    mock_registry.find.assert_called_once_with(
        display_name="my-skill",
        resource_type=RegistryResourceType.SKILL,
    )
    mock_registry.get_skill_async.assert_called_once_with(
        "projects/test-project/locations/us-central1/skills/my-skill"
    )


@patch("app.classes.skills_helper.RegistryHelper")
def test_skills_helper_get_skills_not_found(mock_registry_helper_cls, mock_settings) -> None:
    """Verifies that get_skills raises ValueError if a skill is not found in the registry."""
    mock_registry = mock_registry_helper_cls.return_value
    mock_registry.find.return_value = []

    helper = SkillsHelper(settings=mock_settings, skills=["missing-skill"])
    with pytest.raises(ValueError, match="Skill 'missing-skill' not found in registry"):
        helper.get_skills()


@patch("app.classes.skills_helper.RegistryHelper")
def test_skills_helper_get_skills_multiple_found_success(mock_registry_helper_cls, mock_settings) -> None:
    """Verifies that get_skills resolves all skills if multiple match the search string."""
    mock_registry = mock_registry_helper_cls.return_value
    mock_registry.find.return_value = [
        {"name": "projects/test-project/locations/us-central1/skills/skill-1"},
        {"name": "projects/test-project/locations/us-central1/skills/skill-2"},
    ]

    mock_skill_1 = MagicMock()
    mock_skill_2 = MagicMock()

    async def mock_get_async(registered_name):
        if registered_name == "projects/test-project/locations/us-central1/skills/skill-1":
            return mock_skill_1
        if registered_name == "projects/test-project/locations/us-central1/skills/skill-2":
            return mock_skill_2
        return None

    setup_mock_registry(mock_registry, get_skill_async_side_effect=mock_get_async)

    helper = SkillsHelper(settings=mock_settings, skills=["ambiguous-skill"])
    resolved = helper.get_skills()

    assert resolved == [mock_skill_1, mock_skill_2]
    mock_registry.find.assert_called_once_with(
        display_name="ambiguous-skill",
        resource_type=RegistryResourceType.SKILL,
    )
    assert mock_registry.get_skill_async.call_count == 2



@patch("app.classes.skills_helper.RegistryHelper")
def test_skills_helper_get_skills_cannot_be_resolved(mock_registry_helper_cls, mock_settings) -> None:
    """Verifies that get_skills raises ValueError if registry.get_skill_async returns None."""
    mock_registry = mock_registry_helper_cls.return_value
    mock_registry.find.return_value = [{"name": "projects/test-project/locations/us-central1/skills/unresolvable-skill"}]
    setup_mock_registry(mock_registry, get_skill_async_return=None)

    helper = SkillsHelper(settings=mock_settings, skills=["unresolvable-skill"])
    with pytest.raises(ValueError, match="Skill 'projects/test-project/locations/us-central1/skills/unresolvable-skill' could not be resolved from registry"):
        helper.get_skills()


@patch("app.classes.skills_helper.RegistryHelper")
def test_skills_helper_get_skills_fqn_success(mock_registry_helper_cls, mock_settings) -> None:
    """Verifies that get_skills correctly resolves a fully qualified skill name directly."""
    mock_registry = mock_registry_helper_cls.return_value
    mock_skill_obj = MagicMock()
    setup_mock_registry(mock_registry, get_skill_async_return=mock_skill_obj)

    fqn = "projects/test-project/locations/us-central1/skills/my-skill"
    helper = SkillsHelper(settings=mock_settings, skills=[fqn])
    resolved = helper.get_skills()

    assert resolved == [mock_skill_obj]
    mock_registry.find.assert_not_called()
    mock_registry.get_skill_async.assert_called_once_with(fqn)


@patch("app.classes.skills_helper.RegistryHelper")
def test_skills_helper_get_skills_fqn_cannot_be_resolved(mock_registry_helper_cls, mock_settings) -> None:
    """Verifies that get_skills raises ValueError if an FQN skill cannot be resolved."""
    mock_registry = mock_registry_helper_cls.return_value
    setup_mock_registry(mock_registry, get_skill_async_return=None)

    fqn = "projects/test-project/locations/us-central1/skills/my-skill"
    helper = SkillsHelper(settings=mock_settings, skills=[fqn])
    with pytest.raises(ValueError, match="Skill 'projects/test-project/locations/us-central1/skills/my-skill' could not be resolved from registry"):
        helper.get_skills()

