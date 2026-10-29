from app.api.v1.agents import AgentInfo, AgentListResponse


async def list_agent_service() -> AgentListResponse:
    return AgentListResponse(
        agents=[
            AgentInfo(
                agent_id="agent_chat",
                name="通用聊天助手",
                description="用于普通 AI Chat 场景",
            ),
            AgentInfo(
                agent_id="agent_rag",
                name="知识库问答助手",
                description="用于企业知识库问答场景",
            ),
        ]
    )