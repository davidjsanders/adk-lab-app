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

import logging
import urllib.request
from urllib.error import URLError

logger = logging.getLogger(__name__)

def _fetch_metadata(path: str) -> str | None:
    """
    Fetches metadata from the Google Cloud metadata server.
    
    Args:
        path: The metadata path to fetch (e.g., "/computeMetadata/v1/project/numeric-project-id")
    
    Returns:
        The metadata value as a string, or None if it could not be fetched.
    """
    req = urllib.request.Request(
        f"http://metadata.google.internal{path}",
        headers={"Metadata-Flavor": "Google"}
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.read().decode("utf-8").strip()
    except URLError as e:
        logger.debug(f"Failed to fetch metadata from {path}: {e}")
        return None

def get_project_number() -> str | None:
    """
    Gets the Google Cloud project number from the metadata server.
    
    Returns:
        The project number as a string, or None if it could not be fetched.
    """
    return _fetch_metadata("/computeMetadata/v1/project/numeric-project-id")

def get_instance_region() -> str | None:
    """
    Gets the region (e.g., us-central1) from the metadata server.
    
    Returns:
        The region as a string, or None if it could not be fetched.
    """
    region_full = _fetch_metadata("/computeMetadata/v1/instance/region")
    if region_full:
        # Expected format: projects/123456789/regions/us-central1
        return region_full.split("/")[-1]
    return None
