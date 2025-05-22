
"""rag实现-openai-knn

1. 基于openai实现knn的rag检索
2. 多embedding进行检索问答
3. 具体代码，可参考 [openai-KNN-RAG.ipynb](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/integrations/openai/openai-KNN-RAG.ipynb)
4. 数据集获取方式

```python
import wget, zipfile
embeddings_url = "https://cdn.openai.com/API/examples/data/vector_database_wikipedia_articles_embedded.zip"
wget.download(embeddings_url)
with zipfile.ZipFile("vector_database_wikipedia_articles_embedded.zip", "r") as zip_ref:
    zip_ref.extractall("datas")
```
"""

from __init__ import client, model
from elasticsearch import helpers
import json
from openai import OpenAI
import pandas as pd
import numpy as np

def dataframe_to_bulk_actions(df):
    """批量写入到es"""
    for index, row in df.iterrows():
        yield {
            "_index": "wikipedia_vector_index",
            "_id": row["id"],
            "_source": {
                "url": row["url"],
                "title": row["title"],
                "text": row["text"],
                "title_vector": json.loads(row["title_vector"]),
                "content_vector": json.loads(row["content_vector"]),
                "vector_id": row["vector_id"],
            },
        }



def data2es(index_name = "wikipedia_vector_index", df = ""):
    """批量写入数据到es
    
    Args:
        index_name (str): 待写入index名称
        df (df): 待写入数据集
    """

    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name, ignore_unavailable=True)
    index_mapping = {
        "properties": {
            "title_vector": {
                "type": "dense_vector",
                "dims": 1536,
                "index": "true",
                "similarity": "cosine",
            },
            "content_vector": {
                "type": "dense_vector",
                "dims": 1536,
                "index": "true",
                "similarity": "cosine",
            },
            "text": {"type": "text"},
            "title": {"type": "text"},
            "url": {"type": "keyword"},
            "vector_id": {"type": "long"},
        }
    }
    client.indices.create(index=index_name, mappings=index_mapping)

    start = 0
    end = len(df)
    batch_size = 100
    for batch_start in range(start, end, batch_size):
        batch_end = min(batch_start + batch_size, end)
        batch_dataframe = df.iloc[batch_start:batch_end]
        actions = dataframe_to_bulk_actions(batch_dataframe)
        helpers.bulk(client, actions)



def pretty_response(response):
    for hit in response["hits"]["hits"]:
        id = hit["_id"]
        score = hit["_score"]
        title = hit["_source"]["title"]
        text = hit["_source"]["text"]
        pretty_output = f"\nID: {id}\nTitle: {title}\nSummary: {text}\nScore: {score}"
        print(pretty_output)



if __name__ == "__main__":
    wikipedia_dataframe = pd.read_csv(
        "../datas/vector_database_wikipedia_articles_embedded.csv"
    )

    # data2es(index_name = "wikipedia_vector_index", df = wikipedia_dataframe)

    # 1) 基础检索
    response_demo = client.search(
            index="wikipedia_vector_index",
            query={"match": {"text": {"query": "Hummingbird"}}},
        )
    pretty_response(response_demo)

    # 2) 使用openai模型，实现检索问答
    question = "How big is the Atlantic ocean?"
    client = OpenAI(
        api_key="****",
        base_url = "****"
    )

    EMBEDDING_MODEL = "text-embedding-ada-002"
    question_embedding = client.embeddings.create(input=question, model=EMBEDDING_MODEL)
    response = client.search(
        index="wikipedia_vector_index",
        knn={
            "field": "content_vector",
            "query_vector": question_embedding,
            "k": 10,
            "num_candidates": 100,
        },
    )
    pretty_response(response)
    top_hit_summary = response["hits"]["hits"][0]["_source"][
        "text"
    ] 

    summary = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Answer the following question:"
                + question
                + "by using the following text:"
                + top_hit_summary,
            },
        ],
    )

    choices = summary.choices

    for choice in choices:
        print("------------------------------------------------------------")
        print(choice.message.content)
        print("------------------------------------------------------------")