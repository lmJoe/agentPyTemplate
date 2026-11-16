import pytest
from langchain_core.prompts import ChatPromptTemplate

from app.langchain_prompts.registry import (
    LangChainPromptDefinition,
    LangChainPromptRegistry,
    langchain_prompt_registry,
)
from app.langchain_prompts.templates import (
    AGENT_PLANNER_PROMPT,
    ECOMMERCE_CUSTOMER_SERVICE_PROMPT,
    GENERAL_CHAT_PROMPT,
    RAG_QA_PROMPT,
)
from app.prompts.base import PromptScenario


# 构造一个合法的 Prompt 定义，避免每个用例重复样板代码
def _make_definition(
    prompt_id: str = "demo_prompt",
    version: str = "v1",
    enabled: bool = True,
    scenario: PromptScenario = PromptScenario.GENERAL_CHAT,
) -> LangChainPromptDefinition:
    return LangChainPromptDefinition(
        prompt_id=prompt_id,
        name=f"{prompt_id} 测试 Prompt",
        scenario=scenario,
        version=version,
        description="单元测试使用的 Prompt 定义",
        prompt=ChatPromptTemplate.from_messages(
            [
                ("system", "你是一个测试助手。"),
                ("human", "{user_question}"),
            ]
        ),
        enabled=enabled,
    )


# 构造一个只包含用例数据的独立注册表，避免用例之间互相污染
def _make_registry(*definitions: LangChainPromptDefinition) -> LangChainPromptRegistry:
    registry = LangChainPromptRegistry()
    for definition in definitions:
        registry.register(definition)
    return registry


# 正常场景：不传 version 时使用默认版本 v1
def test_returns_registered_definition_with_default_version():
    definition = _make_definition()
    registry = _make_registry(definition)

    result = registry.get_by_prompt_id("demo_prompt")

    assert result is definition
    assert result.prompt_id == "demo_prompt"
    assert result.version == "v1"
    assert result.enabled is True


# 正常场景：显式传入 version 时返回对应版本
def test_returns_definition_of_explicit_version():
    v1_definition = _make_definition(version="v1")
    v2_definition = _make_definition(version="v2")
    registry = _make_registry(v1_definition, v2_definition)

    assert registry.get_by_prompt_id("demo_prompt", version="v1") is v1_definition
    assert registry.get_by_prompt_id("demo_prompt", version="v2") is v2_definition


# 正常场景：注册多个 Prompt 时只返回被请求的那一个
def test_returns_only_the_requested_prompt_id():
    chat_definition = _make_definition(
        prompt_id="general_chat",
        scenario=PromptScenario.GENERAL_CHAT,
    )
    rag_definition = _make_definition(
        prompt_id="rag_qa",
        scenario=PromptScenario.RAG_QA,
    )
    registry = _make_registry(chat_definition, rag_definition)

    assert registry.get_by_prompt_id("general_chat") is chat_definition
    assert registry.get_by_prompt_id("rag_qa") is rag_definition


# 边界场景：相同 key 重复注册后，返回最后一次注册的定义
def test_latest_registration_wins_for_same_key():
    old_definition = _make_definition()
    new_definition = _make_definition()
    registry = _make_registry(old_definition)
    registry.register(new_definition)

    result = registry.get_by_prompt_id("demo_prompt", version="v1")

    assert result is new_definition
    assert result is not old_definition


# 边界场景：prompt_id 大小写敏感
def test_prompt_id_lookup_is_case_sensitive():
    definition = _make_definition(prompt_id="General_Chat")
    registry = _make_registry(definition)

    assert registry.get_by_prompt_id("General_Chat") is definition

    with pytest.raises(KeyError) as excinfo:
        registry.get_by_prompt_id("general_chat")

    assert excinfo.value.args[0] == "Prompt 不存在：general_chat@v1"


# 边界场景：prompt_id 中的分隔符不会影响查找（注册与查询使用同一套 key 规则）
def test_prompt_id_with_separator_characters_is_supported():
    definition = _make_definition(prompt_id="ecommerce:customer_service")
    registry = _make_registry(definition)

    assert registry.get_by_prompt_id("ecommerce:customer_service") is definition


# 边界场景：空字符串 prompt_id 查不到
def test_empty_prompt_id_raises_key_error():
    registry = _make_registry(_make_definition())

    with pytest.raises(KeyError) as excinfo:
        registry.get_by_prompt_id("")

    assert excinfo.value.args[0] == "Prompt 不存在：@v1"


# 边界场景：空字符串 version 查不到
def test_empty_version_raises_key_error():
    registry = _make_registry(_make_definition())

    with pytest.raises(KeyError) as excinfo:
        registry.get_by_prompt_id("demo_prompt", version="")

    assert excinfo.value.args[0] == "Prompt 不存在：demo_prompt@"


# 边界场景：prompt_id 不会被自动去除首尾空格
def test_whitespace_prompt_id_is_not_trimmed():
    registry = _make_registry(_make_definition())

    with pytest.raises(KeyError) as excinfo:
        registry.get_by_prompt_id(" demo_prompt ")

    assert excinfo.value.args[0] == "Prompt 不存在： demo_prompt @v1"


# 异常场景：prompt_id 未注册
def test_unknown_prompt_id_raises_key_error():
    registry = _make_registry(_make_definition())

    with pytest.raises(KeyError) as excinfo:
        registry.get_by_prompt_id("missing_prompt")

    assert excinfo.value.args[0] == "Prompt 不存在：missing_prompt@v1"


# 异常场景：prompt_id 已注册但 version 不存在
def test_unknown_version_raises_key_error():
    registry = _make_registry(_make_definition(version="v1"))

    with pytest.raises(KeyError) as excinfo:
        registry.get_by_prompt_id("demo_prompt", version="v2")

    assert excinfo.value.args[0] == "Prompt 不存在：demo_prompt@v2"


# 异常场景：Prompt 存在但已被禁用
def test_disabled_prompt_raises_key_error():
    registry = _make_registry(_make_definition(enabled=False))

    with pytest.raises(KeyError) as excinfo:
        registry.get_by_prompt_id("demo_prompt", version="v1")

    assert excinfo.value.args[0] == "Prompt 已禁用：demo_prompt@v1"


# 异常场景：某个版本被禁用时，不影响其他版本的正常查询
def test_disabled_definition_does_not_affect_other_versions():
    disabled_definition = _make_definition(version="v1", enabled=False)
    enabled_definition = _make_definition(version="v2", enabled=True)
    registry = _make_registry(disabled_definition, enabled_definition)

    assert registry.get_by_prompt_id("demo_prompt", version="v2") is enabled_definition

    with pytest.raises(KeyError) as excinfo:
        registry.get_by_prompt_id("demo_prompt", version="v1")

    assert excinfo.value.args[0] == "Prompt 已禁用：demo_prompt@v1"


# 集成场景：全局注册表中的内置 Prompt 都能被正确取到
@pytest.mark.parametrize(
    ("prompt_id", "expected_scenario", "expected_template"),
    [
        ("general_chat", PromptScenario.GENERAL_CHAT, GENERAL_CHAT_PROMPT),
        (
            "ecommerce_customer_service",
            PromptScenario.ECOMMERCE_CUSTOMER_SERVICE,
            ECOMMERCE_CUSTOMER_SERVICE_PROMPT,
        ),
        ("rag_qa", PromptScenario.RAG_QA, RAG_QA_PROMPT),
        ("agent_planner", PromptScenario.AGENT_PLANNER, AGENT_PLANNER_PROMPT),
    ],
)
def test_global_registry_returns_builtin_prompt_definitions(
    prompt_id: str,
    expected_scenario: PromptScenario,
    expected_template: ChatPromptTemplate,
):
    definition = langchain_prompt_registry.get_by_prompt_id(prompt_id)

    assert definition.prompt_id == prompt_id
    assert definition.version == "v1"
    assert definition.scenario == expected_scenario
    assert definition.prompt is expected_template
    assert definition.enabled is True


# 集成场景：全局注册表中不存在的 Prompt 同样抛出 KeyError
def test_global_registry_unknown_prompt_id_raises_key_error():
    with pytest.raises(KeyError) as excinfo:
        langchain_prompt_registry.get_by_prompt_id("not_registered")

    assert excinfo.value.args[0] == "Prompt 不存在：not_registered@v1"
