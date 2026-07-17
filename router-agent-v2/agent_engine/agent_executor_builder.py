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

from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.executor.config import A2aAgentExecutorConfig, ExecuteInterceptor

from .create_runner import create_runner
from .sanitize_events import sanitize_after_agent, sanitize_after_event

logger = logging.getLogger(__name__)

def agent_executor_builder() -> A2aAgentExecutor:
    """Builds and configures the A2A Agent Executor with sanitization and A2UI interceptors."""
    logger.info("Running Agent Executor builder for router-agent-v2")
    interceptor = ExecuteInterceptor(
        after_event=sanitize_after_event,
        after_agent=sanitize_after_agent,
    )
    config = A2aAgentExecutorConfig(execute_interceptors=[interceptor])
    return A2aAgentExecutor(
        runner=create_runner,
        config=config,
    )
