from app.prompts.base import PromptScenario
from app.service.prompt_service import prompt_service


#  通过“通用聊天”场景获取 Prompt，填入用户问题，渲染后打印将要发送给大模型的消息内容。

def main():
    """程序入口：渲染并输出通用聊天 Prompt。"""

    # 根据业务场景查找 Prompt 模板，并传入模板所需变量
    messages = prompt_service.render_by_scenario(
        # 指定使用“通用聊天”场景的 Prompt
        scenario=PromptScenario.GENERAL_CHAT,

        # 用实际值替换 Prompt 模板中的 {user_question}
        variables={
            "user_question": "什么是 Prompt Engineering？",
        },
    )

    # messages 是渲染后的 LLMMessage 列表；
    # 通常可直接传给大模型接口。
    for message in messages:
        # 输出消息角色，例如 system 或 user
        print("role:", message.role)

        # 输出消息内容
        print("content:")
        print(message.content)

        # 分隔每条消息，方便终端阅读
        print("=" * 60)


# 仅当当前文件被直接运行时执行 main()；
# 若该文件被其他模块 import，则不会自动执行。
if __name__ == "__main__":
    main()