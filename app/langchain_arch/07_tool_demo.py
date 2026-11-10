from langchain_core.tools import tool


# 工具的使用

@tool
def query_order(order_id: str) -> str:
  """根据订单号查询订单状态和物流信息"""
  # 自己的业务（如查数据，第三方接口 java ts python）
  if order_id == "10001":
    return "订单10001 已发货，物流公司顺丰，物流单号SF10001，预计3天后送达。"

  if order_id == "10002":
    return "订单10002 已发货，物流公司圆通，物流单号YT10002，预计5天后送达。"

  return f"订单{order_id} 未找到，请检查订单号是否正确。"

def main():
  print("tool name:", query_order.name)
  print("tool description:", query_order.description)
  print("tool args:", query_order.args)

  result = query_order.invoke({
    "order_id": "10003"
  })

  print("result:", result)

if __name__ == "__main__":
  main()