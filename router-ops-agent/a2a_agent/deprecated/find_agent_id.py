import sys
import vertexai
from vertexai.preview import reasoning_engines

def find_agent_id(display_name, project, location):
    """Finds the ID of a Reasoning Engine by display name.
    
    Args:
        display_name: The display name to search for.
        project: The Google Cloud project ID.
        location: The Google Cloud region.

    Returns:
        The resource ID of the engine if found, or None.
    """
    try:
        print("Connecting to Vertex AI...", file=sys.stderr)
        vertexai.init(project=project, location=location)
        print("Fetching Reasoning Engines list (this may take up to 30 seconds)...", file=sys.stderr)
        engines = reasoning_engines.ReasoningEngine.list()
        print("Analyzing display name matches...", file=sys.stderr)
        for eng in engines:
            if eng.display_name == display_name:
                # The resource_name is in format projects/{project}/locations/{location}/reasoningEngines/{id}
                # Return just the ID as expected by adk deploy --agent_engine_id when project and region are set.
                return eng.resource_name.split('/')[-1]
        return None
    except Exception as e:
        print(f"Error listing engines: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: find_agent_id.py <display_name> <project> <location>", file=sys.stderr)
        sys.exit(1)
    
    display_name = sys.argv[1]
    project = sys.argv[2]
    location = sys.argv[3]
    
    agent_id = find_agent_id(display_name, project, location)
    if agent_id:
        print(agent_id)
    else:
        print("", end="") # Print nothing if not found
