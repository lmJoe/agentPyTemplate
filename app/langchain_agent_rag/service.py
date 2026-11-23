from app.core.exceptions import AppException, ErrorCode
from app.core.logging import get_logger
from app.langchain_agent_rag.factory import (
    build_ecommerce_agent_with_rag,
    parse_agent_rag_result,
)
from app.langchain_agent_rag.index import ensure_rag_index
from app.langchain_agent_rag.schemas import AgentRAGRunResponse


# 创建当前模块的日志记录器，用于记录执行开始、成功和失败信息。
logger = get_logger(__name__)

# LangChainAgentRAGService 把一次客服问答需要的步骤集中起来：准备知识库索引、创建 Agent、异步处理用户问题、解析执行结果，并返回统一的数据结构。


class LangChainAgentRAGService:
    """封装电商客服 Agent + RAG 的执行流程。"""

    async def run_ecommerce_agent_rag(
        self,
        user_question: str,
        provider: str = "deepseek",
        model_name: str = "deepseek-chat",
    ) -> AgentRAGRunResponse:
        """处理用户问题，并返回 Agent 的回答、工具调用和知识库来源。"""

        # 记录本次请求使用的模型供应商和模型名称。
        logger.info(
            f"langchain_agent_rag_start provider={provider} model={model_name}"
        )

        try:
            # 确保 RAG 知识库索引已准备好，并保存索引处理结果。
            # 这是同步函数，因此这里不使用 await。
            index_result = ensure_rag_index()

            # 创建包含订单、物流、转人工和知识库检索工具的 Agent。
            agent = build_ecommerce_agent_with_rag(
                provider=provider,
                model_name=model_name,
            )

            # 异步调用 Agent，传入用户问题。
            result = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_question,
                        }
                    ]
                }
            )

            # 将 LangChain 返回结果整理为项目统一的响应模型。
            parsed = parse_agent_rag_result(result)

            # 将索引准备情况放入响应的扩展元数据中。
            parsed.metadata["index"] = index_result

        except Exception as exc:
            # 记录完整异常堆栈，便于排查模型、工具或索引相关问题。
            logger.exception("langchain_agent_rag_failed")

            # 将底层异常包装成项目统一的应用异常，并保留原始异常作为原因。
            raise AppException(
                message="LangChain Agent + RAG 执行失败",
                code=ErrorCode.LLM_CALL_FAILED,
                status_code=500,
                data={
                    "provider": provider,
                    "model": model_name,
                    "error": repr(exc),
                },
            ) from exc

        # 记录执行结果摘要，不记录完整回答内容。
        logger.info(
            f"langchain_agent_rag_success used_tools={parsed.used_tools} "
            f"used_rag={parsed.used_rag} "
            f"tool_count={len(parsed.tool_calls)} "
            f"source_count={len(parsed.sources)}"
        )

        # 返回解析后的统一响应。
        return parsed


# 创建服务实例，供路由或其他业务代码直接调用。
langchain_agent_rag_service = LangChainAgentRAGService()