import os
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from agent import twinkle_hub_agent

PORT = int(os.getenv("PORT", "8081"))
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "costaff-agent-twinkle-hub")

app = to_a2a(twinkle_hub_agent, host=PUBLIC_HOST, port=PORT, protocol="http")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
