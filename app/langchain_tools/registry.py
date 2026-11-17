from langchain_core.tools import BaseTool

from app.langchain_tools.tools import ECOMMERCE_LANGCHAIN_TOOLS


#   构建 LangChain 工具注册中心，Registry 可以统一管理不同场景的工具实例
#   需要按场景管理工具实例，比如

#   电商客服场景：
#   query_order / query_logistics / transfer_human

#   RAG 场景：
#   query_document / search_knowledge_base

#   数据分析场景：
#   query_database / generate_chart

#   管理员场景：
#   update_config / disable_user

class LangChainToolRegistry:

    #   初始化工具注册中心
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    #   注册工具实例
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    #   获取工具实例
    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"工具不存在：{name}")

        return self._tools[name]

    #   获取所有工具实例
    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    #   获取工具名称列表
    def names(self) -> list[str]:
        return list(self._tools.keys())

    #   获取多个工具实例
    def get_many(
        self,
        names: list[str] | None = None,
    ) -> list[BaseTool]:
        if not names:
            return self.list_tools()

        return [
            self.get(name)
            for name in names
        ]


langchain_tool_registry = LangChainToolRegistry()


for item in ECOMMERCE_LANGCHAIN_TOOLS:
    langchain_tool_registry.register(item)