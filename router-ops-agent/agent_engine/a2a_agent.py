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
import os

from vertexai.preview.reasoning_engines import A2aAgent
from .agent_executor_builder import agent_executor_builder
from .build_agent_card import build_agent_card
from .task_store_builder import task_store_builder

# Prevent OpenSSL concurrency bug only when running in remote Reasoning Engine
if (
    os.environ.get("K_SERVICE")
    or os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")
):
    try:
        import OpenSSL.SSL
        OpenSSL.SSL.Context._require_not_used = lambda self: None
    except (ImportError, AttributeError):
        pass

logger = logging.getLogger(__name__)

def get_a2a_agent() -> A2aAgent:
    """Returns the native A2aAgent for Vertex AI Agent Runtime deployment."""
    return A2aAgent(
        agent_card=build_agent_card(),
        agent_executor_builder=agent_executor_builder,
        task_store_builder=task_store_builder
    )
