
"""多语言知识库-分语言检索支持

1. 同一个知识库有多重语言的内容，分语言检索
2. 具体代码，可参考 [04-multilingual](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/search/04-multilingual.ipynb)
"""

from __init__ import client, model
import json
import textwrap


def pretty_response(response):
    if len(response["hits"]["hits"]) == 0:
        print("Your search returned no results.")
    else:
        for hit in response["hits"]["hits"]:
            score = hit["_score"]
            language = hit["_source"]["language"]
            id = hit["_source"]["id"]
            title = hit["_source"]["title"]
            passage = hit["_source"]["passage"]
            print()
            print(f"ID: {id}")
            print(f"Language: {language}")
            print(f"Title: {title}")
            print(f"Passage: {textwrap.fill(passage, 120)}")
            print(f"Score: {score}")



def data2es_multilingual(index_name = "articles", articles = []):
    """批量写入数据到es-多语言
    
    Args:
        index_name (str): 待写入index名称
        articles (list): 待写入数据集, 其中list值为字典
    """
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name, ignore_unavailable=True)

    mappings = {
        "properties": {
            "language": {"type": "keyword"},
            "id": {"type": "keyword"},
            "title": {"type": "text"},
            "passage": {"type": "text"},
            "passage_embedding": {
                "type": "dense_vector",
                "dims": 1024,
                "index": "true",
                "similarity": "cosine",
            },
        }
    }

    client.indices.create(index=index_name, mappings=mappings)

    operations = []
    for article in articles:
        operations.append({"index": {"_index": "articles"}})
        passage = article["passage"]
        passageEmbedding = model.encode(f"passage: {passage}").tolist()
        article["passage_embedding"] = passageEmbedding
        operations.append(article)

    client.bulk(index=index_name, operations=operations, refresh=True)


def query_multilingui(query = "guide", language = "en"):
    """es检索-分语言

    Note:
        1. 分语言实现KNN检索
    """
    knn = {
        "field": "passage_embedding",
        "query_vector": model.encode(f"query: {query}").tolist(),
        "k": 2,
        "num_candidates": 5,
    }

    if language:
        knn["filter"] = {
            "term": {
                "language": language,
            }
        }
    response = client.search(index="articles", knn=knn)
    pretty_response(response)
    return response



if __name__ == "__main__":
    with open("../datas/article.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    # data2es_multilingual(index_name = "articles", articles = articles)
    print("分语言实现KNN检索")
    query_multilingui("health")