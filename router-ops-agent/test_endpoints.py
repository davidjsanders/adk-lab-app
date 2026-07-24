import vertexai
from vertexai.preview.reasoning_engines import ReasoningEngine

project_id = "agentspace-argolis-demo"
location = "us-central1"
agent_id = "7383829160201814016"
vertexai.init(project=project_id, location=location)

resource_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{agent_id}"
remote_agent = ReasoningEngine(resource_name)

print("Agent attributes:", [a for a in dir(remote_agent) if not a.startswith('_')])
print("Operation schemas:")
print(remote_agent.operation_schemas())
