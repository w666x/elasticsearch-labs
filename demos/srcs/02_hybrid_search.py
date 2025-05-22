
"""混合检索-rrf

1. 多策略混合检索实现，关键词 + 语义相似检索
2. rrf倒数排序融合 - Reciprocal rank fusion (RRF)
3. 具体代码，可参考 [02-hybrid-search](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/search/02-hybrid-search.ipynb)
"""

from __init__ import client, model


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



def reciprocal_rank_fusion(lists, k=60, window_size=1000):
    """rrf实现

    RRF 算法实现：融合多个排序列表，生成最终排序

    Args:
        lists(list): 多个排序列表的集合，每个列表中的元素为文档ID（如 ["doc1", "doc2", ...]）
        k (int): 平滑常数（默认60，用于防止除零）
        window_size (int): 仅对前window_size个结果进行处理

    Returns:
         1. 按 RRF 得分降序排列的文档ID列表
         2. 按得分降序排序，得分相同则按文档ID升序
    """
    scores = {}
    for lst in lists:
        for rank, doc in enumerate(lst[:window_size], start=1):
            scores[doc] = scores.get(doc, 0) + 1 / (k + rank)
    sorted_docs = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return sorted_docs




def query_hybird_nook(query = "python programming"):
    """混合检索-ks

    Note:
        1. 语义相似检索 + 关键词检索
        2. rrf, 目前来看是有问题
    """
    response = client.search(
        index="book_index",
        size=5,
        query={"match": {"summary": query}},
        knn={
            "field": "title_vector",
            "query_vector": model.encode(query).tolist(),
            "k": 5,
            "num_candidates": 10,
        },
        rank={"rrf": {
            "window_size": 50,
            "rank_constant": 20
        }},
    )
    pretty_response(response)



def query_hybird(query = "python programming"):
    """混合检索

    Note:
        1. 语义相似检索 + 关键词检索
        2. rrf, 目前来看是有问题
    """
    response_keyword = client.search(
        index="book_index",
        size=5,
        query={"match": {"summary": query}}
    )
    list_keyword = [hit["_id"] for hit in response_keyword["hits"]["hits"]]

    response_sema = client.search(
        index="book_index",
        size=5,
        knn={
            "field": "title_vector",
            "query_vector": model.encode(query).tolist(),
            "k": 5,
            "num_candidates": 10,
        }
    )
    list_vector = [hit["_id"] for hit in response_sema["hits"]["hits"]]
    response = reciprocal_rank_fusion([list_keyword, list_vector])
    return response

if __name__ == "__main__":
    print("混合检索")
    sorted_docid = query_hybird()
    print(sorted_docid)