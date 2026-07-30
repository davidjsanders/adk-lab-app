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

"""Unit tests for activate_skills helper."""

from unittest.mock import MagicMock, patch
import pytest

from app.helpers.activate_skills import activate_skill


def test_activate_skill_success() -> None:
    """Verifies that activate_skill fetches revisions and patches targetState and defaultRevision."""
    # Mock authentication
    mock_credentials = MagicMock()
    mock_credentials.valid = True
    mock_credentials.token = "dummy-token"

    with patch(
        "google.auth.default", return_value=(mock_credentials, "test-project")
    ):
        # Mock httpx.get to return a list of revisions
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "skillRevisions": [
                {
                    "name": "projects/test-project/locations/us-central1/skills/private-test-skill/revisions/rev-1",
                    "state": "ACTIVE",
                }
            ]
        }

        # Mock httpx.patch response
        mock_patch_response = MagicMock()
        mock_patch_response.status_code = 200

        with patch("httpx.get", return_value=mock_get_response) as mock_get:
            with patch(
                "httpx.patch", return_value=mock_patch_response
            ) as mock_patch:
                success = activate_skill(
                    project_id="test-project",
                    location="us-central1",
                    skill_id="test-skill",
                )

                assert success is True

                # Assert httpx.get was called with the correct revisions endpoint URL
                mock_get.assert_called_once()
                args_get, _ = mock_get.call_args
                assert (
                    args_get[0]
                    == "https://agentregistry.googleapis.com/v1alpha/projects/test-project/locations/us-central1/skills/private-test-skill/revisions"
                )

                # Assert httpx.patch was called with correct body
                mock_patch.assert_called_once()
                args_patch, kwargs_patch = mock_patch.call_args
                assert (
                    args_patch[0]
                    == "https://agentregistry.googleapis.com/v1alpha/projects/test-project/locations/us-central1/skills/private-test-skill"
                )
                assert kwargs_patch["params"] == {
                    "updateMask": "defaultRevision,targetState"
                }
                assert (
                    kwargs_patch["json"]["defaultRevision"]
                    == "projects/test-project/locations/us-central1/skills/private-test-skill/revisions/rev-1"
                )
                assert (
                    kwargs_patch["json"]["targetState"] == "TARGET_STATE_ACTIVE"
                )


def test_activate_skill_no_active_revision() -> None:
    """Verifies that activate_skill returns False if no active revisions exist."""
    mock_credentials = MagicMock()
    mock_credentials.valid = True

    with patch(
        "google.auth.default", return_value=(mock_credentials, "test-project")
    ):
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        # Revisions are in CREATING state (not ACTIVE)
        mock_get_response.json.return_value = {
            "skillRevisions": [
                {
                    "name": "projects/test-project/locations/us-central1/skills/private-test-skill/revisions/rev-1",
                    "state": "CREATING",
                }
            ]
        }

        with patch("httpx.get", return_value=mock_get_response):
            success = activate_skill(
                project_id="test-project",
                location="us-central1",
                skill_id="test-skill",
            )
            assert success is False
