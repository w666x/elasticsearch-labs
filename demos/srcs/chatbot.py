
"""langchain实现es的chat功能

1. 聊天机器人基于 LangChain 的 ConversationalRetrievalChain 实现，具备以下能力
    - 自然语言问答：支持用户使用日常语言提问
    - 基于 Elasticsearch 的混合搜索：在 Elasticsearch 中执行混合搜索（关键词 + 语义），精准定位相关文档
    - 答案提取与摘要生成：通过 OpenAI 大型语言模型 (LLM) 提炼和总结答案
    - 多轮对话记忆：保留上下文语境，支持连续追问
2. openai版本差异，咋不考虑复现
3. 具体代码，可参考 [chatbot.ipynb](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/generative-ai/chatbot.ipynb)
"""

