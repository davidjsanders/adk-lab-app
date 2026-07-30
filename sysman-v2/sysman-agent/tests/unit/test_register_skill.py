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

"""Unit tests for register_skill helper."""

import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from app.helpers.register_skill import register_skill


def test_register_skill_success() -> None:
    """Verifies that register_skill correct packages and uploads the skill."""
    # Create a temporary directory containing SKILL.md
    with tempfile.TemporaryDirectory() as tmp_dir:
        skill_md_path = os.path.join(tmp_dir, "SKILL.md")
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(
                "---\nname: my-cool-skill\ndescription: Test description\n---\nBody"
            )

        # Mock authentication
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.token = "dummy-token"

        with patch(
            "google.auth.default", return_value=(mock_credentials, "test-project")
        ):
            # Mock httpx.post call
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "projects/test-project/locations/us-central1/skills/my-cool-skill"
            }

            with patch("httpx.post", return_value=mock_response) as mock_post:
                res = register_skill(
                    skill_dir=tmp_dir,
                    project_id="test-project",
                    location="us-central1",
                    skill_id="my-cool-skill",
                )

                # Assert result
                assert (
                    res["name"]
                    == "projects/test-project/locations/us-central1/skills/my-cool-skill"
                )

                # Verify httpx.post arguments
                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                assert (
                    args[0]
                    == "https://agentregistry.googleapis.com/v1alpha/projects/test-project/locations/us-central1/skills"
                )
                assert kwargs["params"] == {"skillId": "my-cool-skill"}
                assert kwargs["json"]["type"] == "SIMPLE"
                assert kwargs["json"]["targetState"] == "TARGET_STATE_DRAFT"
                assert "initialRevision" in kwargs["json"]
                assert "archiveUploadSource" in kwargs["json"]["initialRevision"]
                assert "archiveContent" in kwargs["json"]["initialRevision"]["archiveUploadSource"]
                assert kwargs["json"]["displayName"] == "my-cool-skill"
                assert kwargs["json"]["description"] == "Test description"


def test_register_skill_already_exists_revision_upload() -> None:
    """Verifies that register_skill fallback to uploading a new revision if skill already exists."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        skill_md_path = os.path.join(tmp_dir, "SKILL.md")
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(
                "---\nname: my-cool-skill\ndescription: Test description\n---\nBody"
            )

        # Mock authentication
        mock_credentials = MagicMock()
        mock_credentials.valid = True

        with patch(
            "google.auth.default", return_value=(mock_credentials, "test-project")
        ):
            # Create responses:
            # 1. POST skill container -> returns 409 Conflict
            mock_post_409 = MagicMock()
            mock_post_409.status_code = 409

            # 2. POST skill revision -> returns 200 OK
            mock_post_rev_200 = MagicMock()
            mock_post_rev_200.status_code = 200
            mock_post_rev_200.json.return_value = {
                "name": "projects/test-project/locations/us-central1/skills/private-my-cool-skill/revisions/rev-2"
            }

            with patch(
                "httpx.post", side_effect=[mock_post_409, mock_post_rev_200]
            ) as mock_post:
                res = register_skill(
                    skill_dir=tmp_dir,
                    project_id="test-project",
                    location="us-central1",
                    skill_id="my-cool-skill",
                )

                assert (
                    res["name"]
                    == "projects/test-project/locations/us-central1/skills/private-my-cool-skill/revisions/rev-2"
                )

                # Check that both POST calls were made
                assert mock_post.call_count == 2

                # First call was to create the container
                first_call = mock_post.call_args_list[0]
                assert (
                    first_call[0][0]
                    == "https://agentregistry.googleapis.com/v1alpha/projects/test-project/locations/us-central1/skills"
                )

                # Second call was to create a revision
                second_call = mock_post.call_args_list[1]
                assert (
                    second_call[0][0]
                    == "https://agentregistry.googleapis.com/v1alpha/projects/test-project/locations/us-central1/skills/private-my-cool-skill/revisions"
                )
                assert "archiveUploadSource" in second_call[1]["json"]


def test_register_skill_invalid_dir() -> None:
    """Verifies that register_skill raises ValueError for non-existent directories."""
    with pytest.raises(ValueError) as exc_info:
        register_skill(
            skill_dir="/non/existent/path/123",
            project_id="test-project",
            location="us-central1",
            skill_id="my-cool-skill",
        )
    assert "is not a valid directory" in str(exc_info.value)

