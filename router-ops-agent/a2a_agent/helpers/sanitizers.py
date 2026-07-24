from typing import Any
from enum import Enum

def sanitize_value(val: Any) -> Any:
    if isinstance(val, Enum):
        return val.value
    if isinstance(val, dict):
        return {k: sanitize_value(v) for k, v in val.items()}
    if isinstance(val, list | tuple):
        return [sanitize_value(x) for x in val]
    return val

def sanitize_event(event: Any) -> None:
    if hasattr(event, "metadata") and event.metadata:
        event.metadata = sanitize_value(event.metadata)
    
    if hasattr(event, "status") and event.status:
        if hasattr(event.status, "message") and event.status.message:
            if event.status.message.metadata:
                event.status.message.metadata = sanitize_value(event.status.message.metadata)
            if event.status.message.parts:
                for part in event.status.message.parts:
                    if hasattr(part, "root") and part.root:
                        if hasattr(part.root, "data") and part.root.data:
                            part.root.data = sanitize_value(part.root.data)
                        if hasattr(part.root, "metadata") and part.root.metadata:
                            part.root.metadata = sanitize_value(part.root.metadata)

    if hasattr(event, "artifact") and event.artifact:
        if event.artifact.metadata:
            event.artifact.metadata = sanitize_value(event.artifact.metadata)
        if event.artifact.parts:
            for part in event.artifact.parts:
                if hasattr(part, "root") and part.root:
                    if hasattr(part.root, "data") and part.root.data:
                        part.root.data = sanitize_value(part.root.data)
                    if hasattr(part.root, "metadata") and part.root.metadata:
                        part.root.metadata = sanitize_value(part.root.metadata)

async def sanitize_after_event(executor_context, a2a_event, adk_event):
    sanitize_event(a2a_event)
    return a2a_event

async def sanitize_after_agent(executor_context, final_event):
    sanitize_event(final_event)
    return final_event
