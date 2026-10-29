import re
from string import Formatter  # 用于解析 Python 字符串模板中的占位符

from app.llm.schemas import LLMMessage, LLMRole
from app.prompts.base import PromptTemplate




## 把定义好的 Prompt 模板，结合实际传入的变量，渲染成可直接发送给大模型的消息列表
# 流程
# extract_variables：找出模板里使用了哪些变量，例如 {name}。
# validate_prompt_variables：检查 Prompt 声明的必填变量是否已传入。
# render_prompt：将模板中的 {变量名} 替换为实际内容，并生成 LLMMessage 列表。
# mask_prompt_for_log：将内容压缩为单行、限制长度，适合安全地写入日志。

# Prompt 渲染或变量校验失败时使用的自定义异常
class PromptRenderError(Exception):
    pass


def extract_variables(template: str) -> set[str]:
    """
    提取模板中的变量名。

    例如：
        "你好，{name}，今天是 {date}" -> {"name", "date"}
    """
    variables = set()

    # Formatter.parse() 会依次返回：
    # (普通文本, 字段名, 格式说明, 转换标志)
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name:
            variables.add(field_name)

    return variables


def validate_prompt_variables(
    prompt: PromptTemplate,
    variables: dict,
):
    """
    校验 Prompt 声明的必填变量是否都已提供且值不为 None。

    若缺失变量，则抛出 PromptRenderError。
    """
    missing = []

    for name in prompt.required_variables:
        # 未传入变量，或变量值为 None，均视为缺失
        if name not in variables or variables[name] is None:
            missing.append(name)

    if missing:
        raise PromptRenderError(
            f"Prompt 缺少必填变量：{', '.join(missing)}"
        )


def render_prompt(
    prompt: PromptTemplate,
    variables: dict,
) -> list[LLMMessage]:
    """
    将 PromptTemplate 中的消息模板替换为实际变量值，
    并转换为 LLMMessage 列表。

    例如：
        模板：'你好，{name}'
        variables：{'name': '小明'}
        渲染后：'你好，小明'
    """
    # 先校验模型声明的必填变量
    validate_prompt_variables(prompt, variables)

    rendered_messages: list[LLMMessage] = []

    # 逐条渲染 Prompt 中的消息模板
    for message_template in prompt.messages:
        try:
            # 使用 variables 替换模板中的 {变量名}
            content = message_template.template.format(**variables)
        except KeyError as exc:
            # 若模板内存在未提供的变量，转换为业务异常
            raise PromptRenderError(
                f"Prompt 模板变量未提供：{exc}"
            ) from exc

        # 将 PromptRole 转为 LLMRole，并清除内容首尾空白
        rendered_messages.append(
            LLMMessage(
                role=LLMRole(message_template.role.value),
                content=content.strip(),
            )
        )

    return rendered_messages


def mask_prompt_for_log(content: str, max_length: int = 120) -> str:
    """
    将 Prompt 内容转换为适合日志记录的简短单行文本。

    - 连续空白字符（换行、制表符、多个空格）会合并成一个空格
    - 内容超过 max_length 时会截断并追加省略号
    """
    # 将所有连续空白字符规范为一个空格
    content = re.sub(r"\s+", " ", content).strip()

    # 内容长度未超限，直接返回
    if len(content) <= max_length:
        return content

    # 超出长度时截断，避免日志过长
    return content[:max_length] + "..."