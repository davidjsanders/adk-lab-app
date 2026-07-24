from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.executor.config import A2aAgentExecutorConfig, ExecuteInterceptor

from .create_runner import create_runner
from .sanitizers import (
    sanitize_after_agent,
    sanitize_after_event,
)

def executor_builder():
    interceptor = ExecuteInterceptor(
        after_event=sanitize_after_event,
        after_agent=sanitize_after_agent,
    )
    config = A2aAgentExecutorConfig(execute_interceptors=[interceptor])
    return A2aAgentExecutor(
        runner=create_runner,
        config=config
    )
