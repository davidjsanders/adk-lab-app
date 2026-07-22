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

"""Attach A2A (Agent2Agent) endpoints to the FastAPI app.

func:`attach_a2a_routes` registers the dynamic
agent-card endpoint and the JSON-RPC endpoint so the same app serves A2A
alongside the adk_api routes, reachable by A2A clients and Gemini Enterprise A2A
registration.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)
from typing import TYPE_CHECKING, Any

import base64
import json
import re
import uuid

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import TaskStore
from a2a.types import (
    AgentCapabilities,
    AgentExtension,
    DataPart,
    Part,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.executor.config import A2aAgentExecutorConfig, ExecuteInterceptor
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

if TYPE_CHECKING:
    from fastapi import FastAPI
    from google.adk.agents import BaseAgent
    from google.adk.runners import Runner

# URI advertised on the agent card describing the executor extension shipped
# by ADK. Kept as a module-level constant so callers can override or extend
# the capabilities list when needed.
_ADK_AGENT_EXECUTOR_EXTENSION_URI = (
    "https://google.github.io/adk-docs/a2a/a2a-extension/"
)


def _default_capabilities() -> AgentCapabilities:
    """Returns the default A2A capabilities used by scaffolded projects."""
    return AgentCapabilities(
        streaming=True,
        extensions=[
            AgentExtension(
                uri="https://a2ui.org/a2a-extension/a2ui/v0.8",
                description="Ability to render A2UI",
                params={
                    "supportedCatalogIds": [
                        "https://a2ui.org/specification/v0_8/standard_catalog_definition.json"
                    ]
                },
            ),
            AgentExtension(
                uri=_ADK_AGENT_EXECUTOR_EXTENSION_URI,
                description=("Ability to use the new agent executor implementation"),
            ),
        ],
    )


async def _a2ui_after_event(
    ctx: Any,
    a2a_event: Any,
    adk_event: Any,
) -> Any:
    """Interceptor hook that converts <a2ui-json> string payloads into DataParts with application/json+a2ui mimeType."""
    parts = []

    if isinstance(a2a_event, TaskStatusUpdateEvent) and a2a_event.status and a2a_event.status.message:
        parts = a2a_event.status.message.parts
    elif isinstance(a2a_event, TaskArtifactUpdateEvent) and a2a_event.artifact:
        parts = a2a_event.artifact.parts

    if not parts:
        return a2a_event

    new_parts = []
    for part in parts:
        part_root = getattr(part, "root", part)
        if isinstance(part_root, TextPart) and part_root.text:
            text = part_root.text
            if "<a2ui-json>" in text and "</a2ui-json>" in text:
                match = re.search(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                    try:
                        parsed_json = json.loads(json_str)
                        if isinstance(parsed_json, list):
                            for msg in parsed_json:
                                a2ui_part = Part(
                                    root=DataPart(
                                        data=msg,
                                        metadata={"mimeType": "application/json+a2ui"},
                                    )
                                )
                                new_parts.append(a2ui_part)
                        else:
                            a2ui_part = Part(
                                root=DataPart(
                                    data=parsed_json,
                                    metadata={"mimeType": "application/json+a2ui"},
                                )
                            )
                            new_parts.append(a2ui_part)
                        continue
                    except Exception as exc:
                        logger.error(f"Error parsing <a2ui-json> in interceptor: {exc}")
        new_parts.append(part)

    if isinstance(a2a_event, TaskStatusUpdateEvent) and a2a_event.status and a2a_event.status.message:
        a2a_event.status.message.parts = new_parts
    elif isinstance(a2a_event, TaskArtifactUpdateEvent) and a2a_event.artifact:
        a2a_event.artifact.parts = new_parts

    return a2a_event


a2ui_converter_interceptor = ExecuteInterceptor(after_event=_a2ui_after_event)


import requests


def _get_cloud_run_base_url() -> str | None:
    """Dynamically resolves Cloud Run service base URL using GCP metadata server and env vars.

    Format: https://<service_name>-<project_number>.<location>.run.app
    """
    if os.getenv("APP_URL"):
        logger.info("Using APP_URL env var: %s", os.getenv("APP_URL"))
        return os.getenv("APP_URL")

    service_name = os.environ.get("K_SERVICE", "router-ops-agent")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"

    try:
        headers = {"Metadata-Flavor": "Google"}
        resp = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id",
            headers=headers,
            timeout=3,
        )
        logger.info("Metadata server response status: %s, text: %s", resp.status_code, resp.text)
        if resp.status_code == 200:
            project_number = resp.text.strip()
            url = f"https://{service_name}-{project_number}.{location}.run.app"
            logger.info("Resolved Cloud Run base URL: %s", url)
            return url
    except Exception as exc:
        logger.warning("_get_cloud_run_base_url failed: %s", exc)

    return None


async def attach_a2a_routes(
    app: FastAPI,
    *,
    agent: BaseAgent,
    runner: Runner,
    task_store: TaskStore,
    rpc_path: str,
    capabilities: AgentCapabilities | None = None,
    agent_version: str | None = None,
    app_url: str | None = None,
) -> None:
    """Register A2A routes (JSON-RPC + agent-card endpoints) under ``rpc_path``.

    Builds a dynamic agent card from ``agent`` and mounts the routes on ``app``.
    The ``runner`` should share the session/artifact/memory services with the
    standard ADK path. ``capabilities``, ``agent_version``, and ``app_url``
    override their defaults (streaming + ADK extension, ``AGENT_VERSION``,
    ``APP_URL``). Call once per app — typically in a FastAPI ``lifespan``, since
    the card is built asynchronously; repeated calls register duplicate routes.
    """
    resolved_app_url = app_url or _get_cloud_run_base_url() or "http://0.0.0.0:8000"
    resolved_agent_version = agent_version or os.getenv("AGENT_VERSION", "0.1.0")
    resolved_capabilities = capabilities or _default_capabilities()

    agent_card = await AgentCardBuilder(
        agent=agent,
        capabilities=resolved_capabilities,
        rpc_url=f"{resolved_app_url}{rpc_path}",
        agent_version=resolved_agent_version,
    ).build()

    agent_card.icon_url = os.getenv(
        "AGENT_ICON_URL",
        "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/wifi/default/24px.svg",
    )

    executor_config = A2aAgentExecutorConfig(
        execute_interceptors=[
            a2ui_converter_interceptor,
        ]
    )

    request_handler = DefaultRequestHandler(
        agent_executor=A2aAgentExecutor(runner=runner, config=executor_config),
        task_store=task_store,
    )

    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)
    a2a_app.add_routes_to_app(
        app,
        agent_card_url=f"{rpc_path}{AGENT_CARD_WELL_KNOWN_PATH}",
        rpc_url=rpc_path,
        extended_agent_card_url=f"{rpc_path}{EXTENDED_AGENT_CARD_PATH}",
    )
