from langchain_core.messages import HumanMessage, SystemMessage

from app.langchain_models.model_factory import LangChainModelFactory


# 演示 LangChain ChatModel 的作用 
def main():
  model = LangChainModelFactory.create(
    provider="deepseek",
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=2048,
  )

  messages = [
    SystemMessage(content="你是一个专业的AI助手，帮助用户解答问题。"),
    HumanMessage(content="请用三句话解释 LangChain ChatModel。"),
  ]

  response = model.invoke(messages)

  print("content:")
  print(response.content)
  print("response_metadata:")
  print(response.response_metadata)
  print("usage_metadata:")
  print(response.usage_metadata)

if __name__ == "__main__":
  main()


#   response_metadata: {
# 	'token_usage': {
# 		'completion_tokens': 107,
# 		'prompt_tokens': 26,
# 		'total_tokens': 133,
# 		'completion_tokens_details': None,
# 		'prompt_tokens_details': {
# 			'audio_tokens': None,
# 			'cache_write_tokens': None,
# 			'cached_tokens': 0,
# 			'image_tokens': None,
# 			'text_tokens': None
# 		},
# 		'prompt_cache_hit_tokens': 0,
# 		'prompt_cache_miss_tokens': 26
# 	},
# 	'model_provider': 'openai',
# 	'model_name': 'deepseek-flash',
# 	'system_fingerprint': 'bc19ba97cbe016479903222bb1578db6',
# 	'id': 'b0422370-6de9-45df-9b2d-0644e080e724',
# 	'finish_reason': 'stop',
# 	'logprobs': None
# }




# usage_metadata: {
# 	'input_tokens': 26,
# 	'output_tokens': 107,
# 	'total_tokens': 133,
# 	'input_token_details': {
# 		'cache_read': 0
# 	},
# 	'output_token_details': {}
# }