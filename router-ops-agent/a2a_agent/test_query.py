import vertexai
from vertexai.preview.reasoning_engines import ReasoningEngine
from google.cloud.aiplatform_v1beta1 import QueryReasoningEngineRequest

def main():
    project_id = "agentspace-argolis-demo"
    location = "us-central1"
    agent_id = "7383829160201814016"
    
    vertexai.init(project=project_id, location=location)
    
    resource_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{agent_id}"
    print(f"Connecting to Agent Runtime: {resource_name}")
    
    remote_agent = ReasoningEngine(resource_name)
    
    query = "List the routers in the fleet as a table"
    print(f"\nSending query:\n{query}\n")
    
    request_payload = {
        "messages": [
            {
                "role": "user",
                "parts": [{"text": query}]
            }
        ]
    }
    context_payload = {}
    
    try:
        req = QueryReasoningEngineRequest(
            name=resource_name,
            input={"request": request_payload, "context": context_payload},
            class_method="a2a"
        )
        response = remote_agent.execution_api_client.query_reasoning_engine(request=req)
        print("Response received:\n")
        print(response.output)
    except Exception as e:
        print(f"Error querying agent: {e}")

if __name__ == "__main__":
    main()
