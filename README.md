


api==接口层    路由请求 参数校验 处理业务逻辑
schemas==数据模型层，请求和响应模型，参数校验 Swagger 文档
services==业务逻辑层，调用LLM 调用向量数据库 调用外部服务 Agent 组合 repositories
repositories==数据访问层，数据库操作 文件系统操作 redis
        db redis llm tool vector db
modules==数据模型
core==核心配置 日志 异常 常量 安全 初始化配置
dependencies==依赖注入 fastapi 依赖


main.py
└── api/v1/api.py -
    ├── chat.py
    ├── health.py
    ├── conversations.py
    └── rag.py

pgsql 向量数据库
        pgvector
milvus
qdrant
elaticsearch
还有其他的向量数据库


## 项目结构

```text
app/
├── api/              FastAPI 接口层
├── core/             核心配置、常量、日志、异常
├── schemas/          Pydantic 请求与响应模型
├── services/         业务逻辑层
├── repositories/     数据访问层
├── models/           数据库 ORM 模型
└── dependencies/     FastAPI 依赖注入

## 项目启动
uv run uvicorn app.main:app --reload

## API文档
http://127.0.0.1:8000/docs


dependencies
        setting.py 配置以来
        auth.py 认证以来,权限. api key token
        database.py 数据库依赖
        llm.py llm 依赖

fastapi
使用Depends是fastAPI帮我们做的
        1.分析接口函数参数
        2.发现某个参数使用了Depends
        3.调用Depends里面的依赖函数
        4.依赖函数返回的值,作为接口函数的参数
        5.接口函数执行


        有些接口需要管理员才能访问
        查看系统的配置
        查看系统的健康状态
        管理模型
        成本统计

agent_state.py == Agent 状态管理
lock.py == 分布式锁
rate_limit.py == 限流
cache.py == 缓存
keys.py == 密钥管理（统一的key命名）
client.py === 创建redis客户端管理



大模型AI 
后端服务 --- http请求 --- 大模型服务商api --- 模型推理
返回json文本流

什么是AI agent
后端请求参数是什么？

{
        "model":"deepseek-chat",
        "messages":[
                {
                        "role":"user",
                        "content":"什么是AI Agent?"
                }
        ]
}

发给模型api
返回 = answer:{
        "answer":"AI agent是能够理解目标，规划任务并调用工具完成目标的智能体"
}


简易流程
1.用户输入问题
2.前端发送给fastapi
# 后端服务（认证，限流 读取历史的会话消息 读取用户配置的 组装message）
3.fastapi调用组装llm request
4.携带 api ket 请求模型服务商
5.模型推理生成答案
6.返回 response strean chunk 
7.fastapi (spring-boot nestjs)组装 response (解析结果)
8.保存信息 和 useage (用户信息，ai回复，token用量 trace_id 模型信息)
9.返回给前端


后端服务
- 安全控制，上下文组装，成本统计，日志追踪，缓存 错误处理，数据持久化（库）



真实项目
前端，后端技术之上叠加大模型


大模型调用api
- baseURL
- endpoint
- api key
- headers
- request body
- response body
- error handling

##
定义模型的规则
- ai的角色 --- 回答规则，安全便捷，输入格式，业务约束
prompt --- 理解成一个字符串


## 
temperature 
temperature 越低： 回答越稳定，越保守，越确定
temperature 越高： 回答越发散，越随机性，越有创造性
temperature = 0 
业务场景：temperature 小一点
- 客服
- 知识库回答
- 代码生成
- 结构化输出

业务场景：temperature 大一些
- 创意写作
- 营销文案
- 标题生成
- 头脑风暴


## 
max_tokens:1000---1000个token
英文：一个单词可能是一个或多个token
中文：一个字或一个词可能被切成一个或多个token
为什么要限制 man_tokens
  输出长度
  响应耗时
  调用成本
  前端展示

token 和 usage： 关系到成本的统计，用户额度，模型的调用分析，限流计费性能优化
{
        "usage":{
                "prompt_tokens":120,    # 输入
                "completion_tokens":80, # 输出
                "total_tokens":200      # 总的
        }
}
这些内容要存储到数据库中db


## 模型的响应
response 
Chat Completions 
非流式响应
缺点：短文本回答，后台任务结构化输出
如：
{
  "id": "chatcmpl_xxx",
  "object": "chat.completion",
  "created": 1720000000,
  "model": "deepseek-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "AI Agent 是能够理解目标、规划任务并调用工具完成目标的智能体。"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 30,
    "completion_tokens": 40,
    "total_tokens": 70
  }
}

stream
模型边生成便返回 token/chunk
SSE = Server-Sent Events
服务端持续想客户端发送事件
适合大模型流式输出
data: {"choices":[{"delta":{"role":"assistant","content":""}}]}

data: {"choices":[{"delta":{"content":"AI"}}]}

data: {"choices":[{"delta":{"content":" Agent"}}]}

data: {"choices":[{"delta":{"content":" 是"}}]}

data: [DONE]

流式解析
full_answer = ""

async for chunk in stream:
    delta = chunk["choices"][0]["delta"]
    content = delta.get("content")

    if content:
        full_answer += content
        yield content


## openAI - compatible API





### 提示词

可维护
可复用
可版本化
可测试
可组合
可和业务场景绑定

电商客服助手
  我的订单什么时候发货？
  一般：请提供订单号，我帮你查询物流状态

  RAG
  prompt Engineering


  最终解决的问题：
  回答太分散：      加角色，加边界，输出要求
  模型编造事实：    明确说不知道就说不知道
  格式不稳定：      加json Schema / 输出模板
  不符合业务流程：   加业务步骤和规则
  不知道怎么调用工具：明确工具使用条件
  RAG回答乱引用：   明确只能基于文档回答
  Agent 执行混乱：  明确目标，计划，步骤和停止条件
  输出风格不统一：   定义预期，长度，格式

  base.py 
        prompt 基础模板
  renderer.py
        prompt 渲染
  registry.py
        promot 注册表
  ecommerce.py
        电商客服助手
  rag.py
        RAG 助手
  agent.py
        AI Agent 助手
  example.py
        few0shot 示例
