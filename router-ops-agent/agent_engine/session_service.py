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
from typing import Any, Optional
from google.adk.sessions import VertexAiSessionService
from google.adk.sessions.session import Session
from google.adk.sessions.base_session_service import ListSessionsResponse
from google.adk.sessions.vertex_ai_session_service import _quote_filter_literal

logger = logging.getLogger(__name__)

class SessionService(VertexAiSessionService):
    """Wrapper that handles framework-provided session IDs for Vertex AI Agent Runtime.

    Vertex AI Agent Engine generates its own session IDs and currently
    raises an error if an external ID is provided. This wrapper drops
    the external ID to ensure compatibility, and maintains a mapping
    via session state/display_name to allow reuse.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id_mapping = {}

    async def list_sessions(
        self,
        *,
        app_name: str,
        user_id: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> Any:
        """Lists sessions with optional filters for user_id and display_name (context_id)."""
        reasoning_engine_id = self._get_reasoning_engine_id(app_name)

        async with self._get_api_client() as api_client:
            sessions = []
            config = {}
            filters = []
            if user_id is not None:
                filters.append(f"user_id={_quote_filter_literal(user_id)}")
            if display_name is not None:
                filters.append(f"display_name={_quote_filter_literal(display_name)}")

            if filters:
                config["filter"] = " AND ".join(filters)

            sessions_iterator = await api_client.agent_engines.sessions.list(
                name=f"reasoningEngines/{reasoning_engine_id}",
                config=config,
            )

            async for api_session in sessions_iterator:
                sessions.append(
                    Session(
                        app_name=app_name,
                        user_id=api_session.user_id,
                        id=api_session.name.split("/")[-1],
                        state=getattr(api_session, "session_state", None) or {},
                        last_update_time=api_session.update_time.timestamp(),
                    )
                )

        return ListSessionsResponse(sessions=sessions)

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Creates a session while suppressing user-provided session IDs."""
        if state is None:
            state = {}

        if "expire_time" not in kwargs and "expireTime" not in kwargs:
            from datetime import datetime, timedelta, timezone
            kwargs["expire_time"] = datetime.now(timezone.utc) + timedelta(hours=48)
            logger.info("SessionService: Applying 48h expiration to new session")

        context_id = session_id
        if context_id:
            state["_context_id"] = context_id
            kwargs["display_name"] = context_id
            logger.info("SessionService: Mapping context_id %s to display_name", context_id)

        session = await super().create_session(
            app_name=app_name, user_id=user_id, state=state, session_id=None, **kwargs
        )

        if context_id:
            self._id_mapping[context_id] = session.id

        return session

    async def get_session(
        self, *, app_name: str, user_id: str, session_id: str, **kwargs: Any
    ) -> Optional[Any]:
        """Attempts to find a session by ID or mapped context ID."""
        if not session_id:
            return None

        if session_id in self._id_mapping:
            real_id = self._id_mapping[session_id]
            return await super().get_session(
                app_name=app_name, user_id=user_id, session_id=real_id, **kwargs
            )

        try:
            session = await super().get_session(
                app_name=app_name, user_id=user_id, session_id=session_id, **kwargs
            )
            if session:
                return session
        except Exception:
            pass

        try:
            sessions_resp = await self.list_sessions(
                app_name=app_name, user_id=user_id, display_name=session_id
            )
            if sessions_resp.sessions:
                matched_session = sessions_resp.sessions[0]
                self._id_mapping[session_id] = matched_session.id
                return matched_session
        except Exception as e:
            logger.warning("SessionService: Error listing sessions by display_name: %s", e)

        return await self.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id, **kwargs
        )
