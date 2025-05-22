
"""设置规则

1. 可以设置一下规则，es检索的时候，这些规则需要满足
2. 当前es版本，不支持啦
3. 具体代码，可参考 [05-query-rules](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/search/05-query-rules.ipynb)
"""

from __init__ import client, model
import json
import textwrap


def pretty_response(response):
    if len(response["hits"]["hits"]) == 0:
        print("Your search returned no results.")
    else:
        for hit in response["hits"]["hits"]:
            id = hit["_id"]
            score = hit["_score"]
            name = hit["_source"]["name"]
            description = hit["_source"]["description"]
            price = hit["_source"]["price"]
            currency = hit["_source"]["currency"]
            plug_type = hit["_source"]["plug_type"]
            voltage = hit["_source"]["voltage"]
            pretty_output = f"\nID: {id}\nName: {name}\nDescription: {description}\nPrice: {price}\nCurrency: {currency}\nPlug type: {plug_type}\nVoltage: {voltage}\nScore: {score}"
            print(pretty_output)



def pretty_ruleset(response):
    print("Ruleset ID: " + response["ruleset_id"])
    for rule in response["rules"]:
        rule_id = rule["rule_id"]
        type = rule["type"]
        print(f"\nRule ID: {rule_id}\n\tType: {type}\n\tCriteria:")
        criteria = rule["criteria"]
        for rule_criteria in criteria:
            criteria_type = rule_criteria["type"]
            metadata = rule_criteria["metadata"]
            values = rule_criteria["values"]
            print(f"\t\t{metadata} {criteria_type} {values}")
        ids = rule["actions"]["ids"]
        print(f"\tPinned ids: {ids}")


def data2es_rule(index_name = "products_index", articles = []):
    """批量写入数据到es-rules
    
    Args:
        index_name (str): 待写入index名称
        articles (list): 待写入数据集, 其中list值为字典
    """
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name, ignore_unavailable=True)

    operations = []
    for doc in articles:
        operations.append({"index": {"_index": "products_index", "_id": doc["id"]}})
        operations.append(doc["content"])
    client.bulk(index="products_index", operations=operations, refresh=True)


def query_base(query = "reliable wireless charger for iPhone"):
    """es检索

    Note:
        1. 分语言实现KNN检索
    """
    response = client.search(
        index="products_index",
        query={
            "multi_match": {
                "query": query,
                "fields": ["name^5", "description"],
            }
        },
    )
    pretty_response(response)
    return response


def query_rule():
    """nook

    Note:
        1. 应用规则的时候，下面两个条件必须要有1个成立
            - my_query contains the string "wireless charger" AND country is "us"
            - my_query contains the string "wireless charger" AND country is "uk"
        2. 传统query方式 + rules
    """
    client.query_rules.put_ruleset(
        ruleset_id="promotion-rules",
        rules=[
            {
                "rule_id": "us-charger",
                "type": "pinned",
                "criteria": [
                    {
                        "type": "contains",
                        "metadata": "my_query",
                        "values": ["wireless charger"],
                    },
                    {"type": "exact", "metadata": "country", "values": ["us"]},
                ],
                "actions": {"ids": ["us1"]},
            },
            {
                "rule_id": "uk-charger",
                "type": "pinned",
                "criteria": [
                    {
                        "type": "contains",
                        "metadata": "my_query",
                        "values": ["wireless charger"],
                    },
                    {"type": "exact", "metadata": "country", "values": ["uk"]},
                ],
                "actions": {"ids": ["uk1"]},
            },
        ],
    )
    response = client.query_rules.get_ruleset(ruleset_id="promotion-rules")
    pretty_ruleset(response)

    response = client.search(
        index="products_index",
        query={
            "rule_query": {
                "organic": {
                    "multi_match": {
                        "query": "reliable wireless charger for iPhone",
                        "fields": ["name^5", "description"],
                    }
                },
                "match_criteria": {
                    "my_query": "reliable wireless charger for iPhone",
                    "country": "us",
                },
                "ruleset_id": "promotion-rules",
            }
        },
    )

    pretty_response(response)


if __name__ == "__main__":
    with open("../datas/query-rules-data.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    # data2es_rule(index_name = "products_index", articles = articles)
    print("检索")
    query_base()
    # query_rule()