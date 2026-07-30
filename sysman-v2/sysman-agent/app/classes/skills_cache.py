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

"""Configurable local and cloud-native cache manager for ADK Skill models."""

import logging
import pathlib
from typing import Optional

from google.adk.skills import Skill

from app.classes.registry_helper import RegistryHelper
from app.config import settings
from app.models.registry_resource_type import RegistryResourceType


logger = logging.getLogger("sysman-agent.helpers.skills_cache")


class SkillCache:
    """Manages persistent caching of Skill objects to local folders or GCS buckets using Pydantic JSON serialization."""

    def __init__(self, role: str, cache_setting: Optional[str] = None):
        """Initializes the SkillCache.

        Args:
            role: The agent role string (e.g. 'Jira', 'Confluence').
            cache_setting: Local directory path or gs://bucket/prefix URI.
                           Defaults to '/tmp/skills_cache' if empty.
        """
        self.role = role
        # Default cache path to /tmp/skills_cache if not provided
        self.cache_setting = cache_setting or "/tmp/skills_cache"
        self.is_gcs = self.cache_setting.startswith("gs://")


        if self.is_gcs:
            gcs_path = self.cache_setting[5:]
            parts = gcs_path.split("/", 1)
            self.bucket_name = parts[0]
            self.gcs_prefix = parts[1].rstrip("/") if len(parts) > 1 else ""
            self._client = None
            self._bucket = None
        else:
            self.cache_path = pathlib.Path(self.cache_setting)
            self.cache_path.mkdir(parents=True, exist_ok=True)

    @property
    def bucket(self):
        """Lazy-loaded Google Cloud Storage bucket instance."""
        if not self.is_gcs:
            return None
        if self._bucket is None:
            from google.cloud import storage
            self._client = storage.Client()
            self._bucket = self._client.bucket(self.bucket_name)
        return self._bucket

    def _get_cache_key(self, skill_name: str, skill_uid: str) -> str:
        """Generates the cache file name key."""
        short_uid = skill_uid.split("-")[0]
        return f"{skill_name}-{short_uid}.json"

    def get(self, skill_name: str, skill_uid: str) -> Optional[Skill]:
        """Tries to retrieve a Skill model from the cache (local folder or GCS).

        Args:
            skill_name: The display name of the skill.
            skill_uid: The unique version UUID of the skill.

        Returns:
            The reconstructed Skill object on cache hit, or None on cache miss.
        """
        key = self._get_cache_key(skill_name, skill_uid)

        if self.is_gcs:
            try:
                blob_name = f"{self.gcs_prefix}/{key}" if self.gcs_prefix else key
                blob = self.bucket.blob(blob_name)
                if blob.exists():
                    logger.info("GCS Cache HIT: Loading skill %s from gs://%s/%s", skill_name, self.bucket_name, blob_name)
                    json_data = blob.download_as_text(encoding="utf-8")
                    return Skill.model_validate_json(json_data)
            except Exception as e:
                logger.warning("Failed to retrieve skill %s from GCS cache: %s", skill_name, e)
        else:
            file_path = self.cache_path / key
            if file_path.exists():
                logger.info("Local Cache HIT: Loading skill %s from %s", skill_name, file_path)
                try:
                    json_data = file_path.read_text(encoding="utf-8")
                    return Skill.model_validate_json(json_data)
                except Exception as e:
                    logger.warning("Failed to retrieve skill %s from local cache: %s", skill_name, e)

        return None

    def set(self, skill_name: str, skill_uid: str, skill: Skill):
        """Saves a Skill model to the cache (local folder or GCS).

        Args:
            skill_name: The display name of the skill.
            skill_uid: The unique version UUID of the skill.
            skill: The Skill object to cache.
        """
        key = self._get_cache_key(skill_name, skill_uid)
        json_data = skill.model_dump_json()

        if self.is_gcs:
            try:
                blob_name = f"{self.gcs_prefix}/{key}" if self.gcs_prefix else key
                blob = self.bucket.blob(blob_name)
                logger.info("GCS Cache MISS: Saving skill %s to gs://%s/%s", skill_name, self.bucket_name, blob_name)
                blob.upload_from_string(json_data, content_type="application/json")
            except Exception as e:
                logger.error("Failed to upload skill %s to GCS cache: %s", skill_name, e)
        else:
            file_path = self.cache_path / key
            try:
                logger.info("Local Cache MISS: Saving skill %s to %s", skill_name, file_path)
                file_path.write_text(json_data, encoding="utf-8")
            except Exception as e:
                logger.error("Failed to save skill %s to local cache: %s", skill_name, e)

    def get_skills(self) -> list[Skill]:
        """Queries the GCP Agent Registry for matching skills, loading them from cache if available.

        Returns:
            List of loaded Skill objects.
        """
        rh = RegistryHelper(
            project_id=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

        query = (
            f"displayName:{self.role.lower()}* OR "
            f"displayName:common* OR "
            f"displayName:supporting*"
        )
        logger.info("Searching Agent Registry for matching skills: %s", query)


        matching_skills_metadata = rh.find(
            display_name=query, resource_type=RegistryResourceType.SKILL
        )

        skills = []
        for metadata in matching_skills_metadata:
            skill_urn = metadata["name"]
            skill_name = metadata["displayName"]
            skill_uid = metadata["uid"]

            # Try loading from cache
            loaded_skill = self.get(skill_name, skill_uid)

            if loaded_skill:
                skills.append(loaded_skill)
                continue

            # Cache miss: fetch from registry
            logger.info("Cache MISS: Retrieving skill payload from registry: %s", skill_urn)
            skill_obj = rh.get(skill_urn, RegistryResourceType.SKILL)
            if skill_obj:
                skills.append(skill_obj)
                # Write back to cache
                self.set(skill_name, skill_uid, skill_obj)

        return skills

