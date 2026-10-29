# 导入 Token 用量模型
from app.llm.schemas import LLMUsage


def estimate_cost(
    usage: LLMUsage,
    input_price_per_1k: float,
    output_price_per_1k: float,
) -> float:
    # 输入 Token 的费用：
    # 输入 Token 数 ÷ 1000 × 每 1000 输入 Token 的价格
    input_cost = usage.prompt_tokens / 1000 * input_price_per_1k

    # 输出 Token 的费用：
    # 输出 Token 数 ÷ 1000 × 每 1000 输出 Token 的价格
    output_cost = usage.completion_tokens / 1000 * output_price_per_1k

    # 返回总费用
    return input_cost + output_cost


# 模拟一次模型调用的 Token 用量
usage = LLMUsage(
    prompt_tokens=1200,       # 输入 1200 Token
    completion_tokens=800,    # 输出 800 Token
    total_tokens=2000,        # 总计 2000 Token
)


# 传入模型单价，计算费用
cost = estimate_cost(
    usage=usage,
    input_price_per_1k=0.001,    # 每 1000 输入 Token 收费 0.001
    output_price_per_1k=0.002,   # 每 1000 输出 Token 收费 0.002
)


# model_dump() 将 Pydantic 模型转为字典，便于打印或 JSON 返回
print("usage:", usage.model_dump())

# 输出本次调用的总费用
print("cost:", cost)