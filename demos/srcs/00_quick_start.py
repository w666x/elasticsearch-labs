
"""快速写数

1. 涉及es连接，增删查改数据
2. 具体代码，可参考 [00-quick-start](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/search/00-quick-start.ipynb)
"""

from __init__ import client, model
import json


def data2es(index_name = "book_index", books = []):
    """批量写入数据到es
    
    Args:
        index_name (str): 待写入index名称
        books (list): 待写入数据集, 其中list值为字典
    """
    
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name, ignore_unavailable=True)

    # Define the mapping
    mappings = {
        "properties": {
            "title_vector": {
                "type": "dense_vector",
                "dims": 1024,
                "index": "true",
                "similarity": "cosine",
            }
        }
    }

    # Create the index
    client.indices.create(index="book_index", mappings=mappings)

    operations = []
    for book in books:
        operations.append({"index": {"_index": "book_index"}})
        book["title_vector"] = model.encode(book["title"]).tolist()
        operations.append(book)

    client.bulk(index="book_index", operations=operations, refresh=True)




def pretty_response(response):
    """es检索结果格式化展示"""
    if len(response["hits"]["hits"]) == 0:
        print("Your search returned no results.")
    else:
        for hit in response["hits"]["hits"]:
            id = hit["_id"]
            publication_date = hit["_source"]["publish_date"]
            score = hit["_score"]
            title = hit["_source"]["title"]
            summary = hit["_source"]["summary"]
            publisher = hit["_source"]["publisher"]
            num_reviews = hit["_source"]["num_reviews"]
            authors = hit["_source"]["authors"]
            pretty_output = f"\nID: {id}\nPublication date: {publication_date}\nTitle: {title}\nSummary: {summary}\nPublisher: {publisher}\nReviews: {num_reviews}\nAuthors: {authors}\nScore: {score}"
            print(pretty_output)


def es_query(query = "javascript books"):
    """es检索

    Note:
        1. 实现knn向量相似检索
        2. 实现filter进一步筛选
    """
    response = client.search(
        index="book_index",
        knn={
            "field": "title_vector",
            "query_vector": model.encode(query),
            "k": 10,
            "num_candidates": 100,
            "filter": {"term": {"publisher.keyword": "addison-wesley"}},
        },
    )
    return response



if __name__ == "__main__":
    with open("../datas/book_demo.json", "r", encoding="utf-8") as f:
        books = json.load(f)
    data2es(index_name = "book_index", books = books)
    response = es_query()
    pretty_response(response)