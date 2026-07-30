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

import io
import logging
from unittest.mock import AsyncMock, MagicMock, patch
import zipfile

import pytest
import requests

from app.classes.registry_helper import RegistryHelper
from app.models.registry_resource_type import RegistryResourceType


def test_registry_helper_connection_error(caplog) -> None:
    """Verifies that RegistryHelper correctly logs and propagates connection errors."""
    helper = RegistryHelper(project_id="test-project", location="us-central1")

    # Capture the ERROR level logs from registry_helper
    with caplog.at_level(logging.ERROR, logger="app.classes.registry_helper"):
        # Mock the request get to raise a ConnectionError
        with patch.object(
            helper.registry._session,
            "get",
            side_effect=requests.exceptions.ConnectionError("DNS resolution failed"),
        ):
            # Verify that calling helper.get propagates the RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                helper.get(
                    registered_name="dummy-agent",
                    resource_type=RegistryResourceType.AGENT,
                )

            # Verify the root cause is the ConnectionError we injected
            assert isinstance(
                exc_info.value.__cause__, requests.exceptions.ConnectionError
            )

    # Verify that the expected error message was logged at line 111
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "ERROR"
    assert (
        "Error getting agent: projects/test-project/locations/us-central1/agents/dummy-agent"
        in record.message
    )


def test_registry_helper_get_skill_success() -> None:
    """Verifies successful retrieval of a Skill using PatchedGCPSkillRegistry."""
    helper = RegistryHelper(project_id="test-project", location="us-central1")

    # 1. Mock GET skill metadata response
    mock_metadata_response = MagicMock()
    mock_metadata_response.json.return_value = {
        "name": "projects/test-project/locations/us-central1/skills/test-skill",
        "defaultRevision": "projects/test-project/locations/us-central1/skills/test-skill/revisions/rev-1",
    }

    # 2. Mock GET skill revision media response (zipped filesystem containing SKILL.md)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr(
            "SKILL.md",
            "---\nname: test-skill\ndescription: A test skill\n---\nBody of skill",
        )
    zip_bytes = zip_buffer.getvalue()

    mock_media_response = MagicMock()
    mock_media_response.content = zip_bytes

    # Set up the AsyncMock side effect to return metadata first, then the zipped media
    async_mock_get = AsyncMock()
    async_mock_get.side_effect = [mock_metadata_response, mock_media_response]

    with patch("httpx.AsyncClient.get", new=async_mock_get):
        skill = helper.get(
            registered_name="test-skill",
            resource_type=RegistryResourceType.SKILL,
        )

    # Assertions
    assert skill.name == "test-skill"
    assert skill.description == "A test skill"
    assert skill.instructions == "Body of skill"


def test_registry_helper_find_skills_success() -> None:
    """Verifies that RegistryHelper.find successfully searches skills using GCPSkillRegistry."""
    helper = RegistryHelper(project_id="test-project", location="us-central1")

    # Mock response from skills:search endpoint
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        "skills": [
            {
                "name": "projects/test-project/locations/us-central1/skills/private-test-skill",
                "displayName": "test-skill",
                "description": "A test skill",
            }
        ]
    }

    async_mock_get = AsyncMock(return_value=mock_search_response)

    with patch("httpx.AsyncClient.get", new=async_mock_get) as mock_get:
        skills = helper.find(
            display_name="test-skill",
            resource_type=RegistryResourceType.SKILL,
        )

    # Assertions
    assert len(skills) == 1
    assert skills[0]["displayName"] == "test-skill"
    assert skills[0]["description"] == "A test skill"

    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert args[0].endswith(
        "/projects/test-project/locations/us/skills:search"
    )
    assert kwargs["params"] == {"search_string": "test-skill"}


