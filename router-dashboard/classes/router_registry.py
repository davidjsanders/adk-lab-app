"""Fleet Registry Management Class for Router Operations Dashboard Application.

Manages persistent JSON storage (`routers.json`), merges dynamic Cloud Run auto-discoveries,
and handles registration CRUD operations for emulated router nodes.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from classes.router_node import RouterNode
from helpers.cloud_run import discover_cloud_run_routers

logger = logging.getLogger(__name__)


class RouterRegistry:
    """Manages router node persistence, active list querying, and Cloud Run merging.

    Attributes:
        config_path: Path string to JSON registry file.
        project_id: Google Cloud project ID string.
        region: Google Cloud region string.
    """

    def __init__(self, config_path: str = "routers.json", project_id: str = "", region: str = "us-central1") -> None:
        """Initializes a new RouterRegistry instance.

        Args:
            config_path: Relative or absolute path to JSON storage file.
            project_id: Google Cloud project ID string.
            region: Google Cloud region string.
        """
        self.config_path: str = config_path
        self.project_id: str = project_id or os.getenv("GCP_PROJECT", "")
        self.region: str = region or os.getenv("GCP_REGION", "us-central1")

    def load_local_routers(self) -> List[RouterNode]:
        """Loads locally stored router nodes from the JSON registry file.

        Returns:
            List of instantiated RouterNode objects.
        """
        if not os.path.exists(self.config_path):
            return []

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                if isinstance(raw_data, list):
                    nodes: List[RouterNode] = []
                    for item in raw_data:
                        if isinstance(item, dict):
                            try:
                                nodes.append(RouterNode.from_dict(item))
                            except Exception as err:
                                logger.warning(f"Skipping malformed router node record in {self.config_path}: {err}")
                    return nodes
        except Exception as err:
            logger.error(f"Error loading router registry file '{self.config_path}': {err}")

        return []

    def save_local_routers(self, routers: List[RouterNode]) -> bool:
        """Persists a list of RouterNode instances to the local JSON configuration file.

        Args:
            routers: List of RouterNode objects to save.

        Returns:
            True if saving succeeded, False otherwise.
        """
        try:
            data = [node.to_dict() for node in routers]
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as err:
            logger.error(f"Failed persisting router registry to '{self.config_path}': {err}")
            return False

    def get_all_routers(self) -> List[RouterNode]:
        """Retrieves complete list of router nodes merging dynamic Cloud Run service discoveries with local entries.

        Returns:
            Merged list of RouterNode objects representing active router fleet.
        """
        is_local_env = not bool(os.getenv("K_SERVICE"))
        local_nodes = self.load_local_routers()
        if not is_local_env:
            # When running on Cloud Run, do not load local test router nodes from routers.json
            local_nodes = [
                n for n in local_nodes
                if not (n.id.startswith("RTR-LOCAL") or "127.0.0.1" in n.url or "localhost" in n.url or n.source == "LOCAL")
            ]

        cloud_run_raw = discover_cloud_run_routers(self.project_id, self.region)

        # Map local entries by ID for fast lookup
        merged_map: Dict[str, RouterNode] = {node.id: node for node in local_nodes}

        for cr_data in cloud_run_raw:
            cr_id = cr_data["id"]
            if cr_id in merged_map:
                # Update URL, last_deployed, revision, and metadata from active Cloud Run service if available
                existing = merged_map[cr_id]
                existing.url = cr_data["url"]
                existing.source = "CLOUDRUN"
                if cr_data.get("last_deployed"):
                    existing.last_deployed = cr_data["last_deployed"]
                if cr_data.get("revision"):
                    existing.revision = cr_data["revision"]
            else:
                merged_map[cr_id] = RouterNode.from_dict(cr_data)

        return list(merged_map.values())

    def get_router_by_id(self, router_id: str) -> Optional[RouterNode]:
        """Finds a specific router node by its unique identifier string.

        Args:
            router_id: Unique string identifier of target router node.

        Returns:
            RouterNode instance if found, None otherwise.
        """
        all_nodes = self.get_all_routers()
        return next((node for node in all_nodes if node.id == router_id), None)

    get_router = get_router_by_id

    def register_router(self, node: RouterNode) -> bool:
        """Registers or updates a router node in local persistent storage.

        Args:
            node: RouterNode instance to register.

        Returns:
            True if registration succeeded, False otherwise.
        """
        local_nodes = self.load_local_routers()
        updated = False

        for idx, existing in enumerate(local_nodes):
            if existing.id == node.id:
                local_nodes[idx] = node
                updated = True
                break

        if not updated:
            local_nodes.append(node)

        return self.save_local_routers(local_nodes)

    def remove_router(self, router_id: str) -> bool:
        """Removes a router node registration from local persistent storage.

        Args:
            router_id: Unique router node string ID to delete.

        Returns:
            True if entry was removed, False if not found or deletion failed.
        """
        local_nodes = self.load_local_routers()
        filtered = [node for node in local_nodes if node.id != router_id]

        if len(filtered) == len(local_nodes):
            return False

        return self.save_local_routers(filtered)
