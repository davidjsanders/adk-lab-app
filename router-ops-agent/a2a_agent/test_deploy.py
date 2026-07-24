from a2a_agent.models.agent_configuration import AgentConfiguration
from a2a_agent.classes.deployer import Deployer
from a2a_agent.agent import A2A_AGENT
from a2a_agent.models.platform import Platform
ac = AgentConfiguration(
    agent=A2A_AGENT,
    agent_id="7383829160201814016",
    display_name="Router Ops",
    description="Agent managing and assisting with Router operations",
    env_path=".env",
    extra_packages=["app", "a2a_agent"],
    location="us-central1",
    platform=Platform.GOOGLE_CLOUD_AGENT_ENGINE,
    project_id="agentspace-argolis-demo",
    requirements_path="requirements.txt",
    staging_bucket="gs://ae-staging-bucket",
)
d = Deployer(configuration=ac)
d.execute()
