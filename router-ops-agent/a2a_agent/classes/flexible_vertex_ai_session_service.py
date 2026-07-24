# if os.environ.get("K_SERVICE") or os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"):
#     try:
#         import OpenSSL.SSL
#         OpenSSL.SSL.Context._require_not_used = lambda self: None
#     except (ImportError, AttributeError):
#         pass
import logging
from datetime import UTC
from typing import Any

from google.adk.sessions import VertexAiSessionService
from google.adk.sessions.base_session_service import ListSessionsResponse
from google.adk.sessions.session import Session
from google.adk.sessions.vertex_ai_session_service import _quote_filter_literal

logger = logging.getLogger(__name__)

class FlexibleVertexAiSessionService(VertexAiSessionService):
    """Wrapper that handles framework-provided session IDs.

    Vertex AI Agent Engine generates its own session IDs and currently
    raises an error if an external ID is provided. This wrapper drops
    the external ID to ensure compatibility with local dev tools, and
    maintains a mapping via session state to allow reuse.
    """

    def __init__(self, *args, **kwargs):
        """Initializes the FlexibleVertexAiSessionService.

        Sets up an in-memory cache for ID mapping to speed up lookups
        during the process lifetime.
        """
        super().__init__(*args, **kwargs)
        self._id_mapping = {}

    async def list_sessions(
        self,
        *,
        app_name: str,
        user_id: str | None = None,
        display_name: str | None = None,
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
        state: dict[str, Any] | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Creates a session while suppressing user-provided session IDs.

        Args:
            app_name: The name of the application.
            user_id: The ID of the user.
            state: The initial state of the session.
            session_id: The user-provided ID (context ID).
            **kwargs: Standard ADK session metadata.

        Returns:
            The created session object.
        """
        if state is None:
            state = {}

        # REST-compliant Expiration Policy (Defaulting to 48h TTL to satisfy Vertex AI >24h minimum)
        if "expire_time" not in kwargs and "expireTime" not in kwargs:
            from datetime import datetime, timedelta
            kwargs["expire_time"] = datetime.now(UTC) + timedelta(hours=48)
            logger.info(
                "FlexibleVertexAiSessionService: Applying REST-compliant 48h expiration ('expire_time') to new session"
            )

        # 1. Intercept the A2A context_id (passed as session_id by ADK)
        context_id = session_id
        if context_id:
            # Store it in state so we can find it by listing sessions later
            state["_context_id"] = context_id
            # Use it as display_name so it shows up nicely in the GCP Console
            kwargs["display_name"] = context_id
            logger.info(
                "FlexibleVertexAiSessionService: Creating session (mapping context_id: %s to display_name)",
                context_id,
            )

        # 2. Call base class with session_id=None because Vertex AI generates its own numeric IDs
        session = await super().create_session(
            app_name=app_name, user_id=user_id, state=state, session_id=None, **kwargs
        )

        # 3. Cache the mapping locally to avoid listing sessions on the next request
        if context_id:
            self._id_mapping[context_id] = session.id

        return session

    async def get_session(
        self, *, app_name: str, user_id: str, session_id: str, **kwargs: Any
    ) -> Any | None:
        """Attempts to find a session by ID or mapped context ID.

        Args:
            app_name: The name of the application.
            user_id: The ID of the user.
            session_id: The ID of the session or context.
            **kwargs: Additional arguments for session retrieval.

        Returns:
            The session object if found, or automatically created if missing.
        """
        if not session_id:
            return None

        # Stage 1: Check local in-memory mapping cache
        if session_id in self._id_mapping:
            real_id = self._id_mapping[session_id]
            logger.info(
                "FlexibleVertexAiSessionService: Cache hit %s -> %s",
                session_id,
                real_id,
            )
            return await super().get_session(
                app_name=app_name, user_id=user_id, session_id=real_id, **kwargs
            )

        # Stage 2: Try direct lookup in case the caller passed a native Vertex AI session ID
        try:
            session = await super().get_session(
                app_name=app_name, user_id=user_id, session_id=session_id, **kwargs
            )
            if session:
                logger.info(
                    "FlexibleVertexAiSessionService: Direct lookup success for session_id %s",
                    session_id,
                )
                return session
        except Exception:
            pass  # Ignore errors and proceed to search

        # Stage 3: Search user sessions matching the context ID as the display name
        logger.info(
            "FlexibleVertexAiSessionService: Searching user sessions for display_name %s",
            session_id,
        )
        try:
            logger.debug("FlexibleVertexAiSessionService: Starting list_sessions")
            import time
            start_time = time.time()
            sessions_resp = await self.list_sessions(
                app_name=app_name, user_id=user_id, display_name=session_id
            )
            logger.debug(
                "FlexibleVertexAiSessionService: Completed list_sessions in %.4f seconds",
                time.time() - start_time,
            )

            if sessions_resp.sessions:
                matched_session = sessions_resp.sessions[0]
                logger.info(
                    "FlexibleVertexAiSessionService: Found mapping %s -> %s via display_name",
                    session_id,
                    matched_session.id,
                )
                self._id_mapping[session_id] = matched_session.id
                return matched_session
        except Exception as e:
            logger.warning(
                "FlexibleVertexAiSessionService: Error listing sessions by display_name: %s",
                e,
            )

        # Stage 4: If still not found, auto-create it.
        # This ensures the flow never fails due to a missing session.
        logger.info(
            "FlexibleVertexAiSessionService: context_id %s not found. Auto-creating new session.",
            session_id,
        )
        return await self.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id, **kwargs
        )
