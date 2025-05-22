
"""关键词检索

1. 涉及es关键词单(多)字段检索、精确匹配（term/range/prefix)
2. 具体代码，可参考 [01-keyword-querying-filtering](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/search/01-keyword-querying-filtering.ipynb)
"""

from __init__ import client
import json


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


def query_keyword(query = "guide"):
    """es检索

    Note:
        1. 关键词检索，匹配summary这个字段
    """
    response = client.search(
        index="book_index", 
        query={"match": {"summary": {"query": query}}}
    )
    pretty_response(response)
    return response


def query_keyword_multi(query = "javascript"):
    """es检索

    Note:
        1. 多关键词检索，在summary和title这2个字段中进行匹配
        2. 对于 `title^3` 的定义，title匹配的得分会乘以3,
    """
    response = client.search(
        index="book_index", 
        query={"multi_match": {"query": query, "fields": ["summary", "title^3"]}},
    )
    pretty_response(response)
    return response


def query_term():
    """精确匹配
    
    Note:
        1. term精确匹配
        2. range，区间匹配
        3. prefix, 前缀匹配
    """
    print("term匹配")
    response = client.search(
        index="book_index", 
        query={"term": {"publisher.keyword": "addison-wesley"}}
    )
    pretty_response(response)

    print("range匹配")
    response = client.search(
        index="book_index", 
        query={"range": {"num_reviews": {"gte": 45}}}
    )
    pretty_response(response)

    print("prefix匹配")
    response = client.search(
        index="book_index", 
        query={"prefix": {"title": {"value": "java"}}}
    )
    pretty_response(response)
    return response


def query_fuzzy():
    """模糊匹配
    
    Note:
        1. 基于Levenshtein编辑距离
    """
    print("编辑距离匹配")
    response = client.search(
        index="book_index", 
         query={"fuzzy": {"title": {"value": "pyvascript"}}}
    )
    pretty_response(response)
    return response


def query_combine():
    """组合匹配
    
    Note:
        1. bool + must，逻辑AND实现
        2. bool + should，逻辑OR实现
    """
    print("AND多条件匹配")
    response = client.search(
        index="book_index", 
        query={
            "bool": {
                "must": [
                    {"term": {"publisher.keyword": "addison-wesley"}},
                    {"term": {"authors.keyword": "richard helm"}},
                ]
            }
        },
    )
    pretty_response(response)

    print("OR多条件匹配")
    response = client.search(
        index="book_index", 
        query={
            "bool": {
                "should": [
                    {"term": {"publisher.keyword": "addison-wesley"}},
                    {"term": {"authors.keyword": "richard helm"}},
                ]
            }
        },
    )
    pretty_response(response)
    return response



def query_bool():
    """bool逻辑检索"""
    print("filter 精确匹配")
    response = client.search(
        index="book_index", 
        query={"bool": {"filter": [{"term": {"publisher.keyword": "prentice hall"}}]}},
    )
    pretty_response(response)


    print("filter mustnot匹配")
    response = client.search(
        index="book_index", 
        query={"bool": {"must_not": [{"range": {"num_reviews": {"lte": 45}}}]}},
    )
    pretty_response(response)


    print("filter + query匹配")
    response = client.search(
        index="book_index", 
        query={
            "bool": {
                "must": [{"match": {"title": {"query": "javascript"}}}],
                "must_not": [{"range": {"num_reviews": {"lte": 45}}}],
            }
        },
    )
    pretty_response(response)
    return response


if __name__ == "__main__":
    print("单字段关键词匹配")
    query_keyword()
    print("多字段关键词匹配")
    query_keyword_multi()
    print("Term-level精确匹配")
    query_term()
    print("Fuzzy模糊匹配")
    query_fuzzy()
    print("组合检索匹配")
    query_combine()
    print("bool检索匹配")
    query_bool()