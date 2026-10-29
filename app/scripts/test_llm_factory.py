from app.llm.factory import (
    LLMProviderFactory,            # 当前代码中没有使用，可删除
    infer_provider_from_model,
)

# 根据模型名称推断供应商



# 准备多个模型名称进行测试
models = [
    "deepseek-chat",
    "qwen-plus",
    "gpt-4.1-mini",
    "unknown-model",
]


# 逐个模型名称推断对应供应商
for model in models:
    provider = infer_provider_from_model(model)

    # 打印推断结果
    print(model, "=>", provider)