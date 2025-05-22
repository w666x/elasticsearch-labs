
"""es-qa实现

1. 涉及文档切块，入es库，检索问答实现
2. openai==0.28.1，版本差异太大啦
3. 具体代码，可参考 [question-answering.ipynb](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/generative-ai/question-answering.ipynb)
"""

from __init__ import client
from langchain_elasticsearch import ElasticsearchStore
from langchain.embeddings.openai import OpenAIEmbeddings
import json

if __name__ == "__main__":
    with open("../datas/data.json", "r", encoding="utf-8") as f:
        books = json.load(f)
    pass