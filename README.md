# AI 私厨

基于 FastAPI、LangChain、LangGraph 和阿里云 OSS 的 AI 私厨项目。

## 功能

- 用户注册和登录
- OSS 图片直传
- 多模态食材识别
- SSE 流式聊天
- 多会话和历史记录
- 长期饮食偏好记忆
- 食材库存和保质期
- 过敏原安全检查

## 本地运行

```bash
uv sync
uv run uvicorn hello_world.app.main:app --host 127.0.0.1 --port 8001 --reload