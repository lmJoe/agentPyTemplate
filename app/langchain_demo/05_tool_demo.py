from langchain_core.tools import tool

@tool
def query_order(order_id: str) -> str:
  """
  根据订单号查询订单和物流的状态
  """

  if order_id == "123456":
    return "订单号 123456 的状态是：已发货，预计3天后送达。物流公司是：顺丰快递，物流单号是：SF123456789。"
  
  return "订单号 123456 未找到，请检查订单号是否正确。".format(order_id)


def run_tool():
  # 打印名称、描述和参数信息
  print("tool name",query_order.name)
  print("tool description",query_order.description)
  print("tool args",query_order.args)

  result = query_order.invoke({
    "order_id":"123456"
  })

  print("tool result:",result)

if __name__ == "__main__":
  run_tool()