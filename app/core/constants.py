from enum import Enum


# 定义了两组“固定可选值”，避免在项目各处随意写字符串
# DEVELOPMENT：本地开发环境
# TESTING：自动化测试环境
# STAGING：预发布/测试服务器环境
# PRODUCTION：正式生产环境

class AppEnv(str,Enum):
  DEVELOPMENT = "development"
  TESTING = "testing"
  STAGING = "staging"
  PRODUCTION = "production"

class ApiTag:
  HEALTH = "Health"
  CHAT = "Chat"
  CONVERSATIONS = "Conversations"
  RAG = "RAG"
  MODELS = "Models"
  AGENTS = "Agents"
  