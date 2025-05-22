```es8和es7差异还蛮大的, 补充个es8的实战demo吧```

#### 主要内容

1. 通过elasticvue进行增删查改的实现demo
2. 通过python的client的增删查改实现demo


## es提高


### demo

![es_demo](https://cdn.jsdelivr.net/gh/w666x/image/git/es_datademo.png)

1. 本部分代码，需先通过环境变量指定账号密码，再执行哦

```sh
export es_host=**:9200
cd src
# 写入数据到es中的 **book_index** 去，供下述查询使用
python 00_quick_start.py  
# vim ../datas/book_demo.json
```


2. 各写数方式文件大小占比
    - embedding模型为bge-large-zh-v1.5，维度为1024


| 类型 | 磁盘大小 | es大小 | 文件说明 | 
|:-|:-|:-|:-|
| book_demo.json | 3KB | 442KB | 增加1024维向量
| article.json | 4KB  | 316KB | 增加1024维向量
| query-rules-data.json | 1.9KB | 24.8KB  | 直接写入
| vector_database_wikipedia_articles_embedded.csv | 1.7G | 4.28G | 直接写入



### Elasticvue实操


#### 写数


1. 新增数据

```sh
curl -XPOST "${es_host}/_bulk" \
  -H "Content-Type: application/x-ndjson" \
  --data-binary "@article.json"


# vim article.json
{ "index": {"_index": "book_index", "_id": "1001" } }
{ "title": "文档1", "passage": "测试内容1" }
{ "create": { "_index": "book_index" } }
{ "title": "文档2", "passage": "测试内容2"}

# 判断数据是否写进去了
curl -XGET "${es_host}/book_index/_count"
curl -XGET "${es_host}/book_index/_doc/<document_id>"
```

![curl写入数据](https://cdn.jsdelivr.net/gh/w666x/image/git/es_api_write.png)


2. 更新数据-单个
    - 直接在elasticvue操作即可


3. 更新数据-批量


```sh
curl -XPOST "${es_host}/_bulk" \
  -H "Content-Type: application/x-ndjson" \
  --data-binary "@article.json"

# vim article.json
{ "update": {"_index": "book_index", "_id": "1001" } }
{ "doc": {"passage": "测试内容2", "language":"fran"}}
{ "update": {"_index": "book_index", "_id": "39dK6JYBB66JPEoPproL" } }
{ "doc": {"passage": "测试内容2", "language":"fran"}}
```



4. 替换数据
    - 方式1, 显示指定多组数据，进行个替换
    - 方式2, 根据query筛选后，执行script进行替换


```sh
# 方式1， 直接替换
curl -XPOST "${es_host}/_bulk" \
  -H "Content-Type: application/x-ndjson" \
  --data-binary "@article.json"

# vim article.json
{ "index": {"_index": "book_index", "_id": "1001" } }
{ "title": "文档1", "passage": "测试内容3" }
{ "index": { "_index": "book_index"} }
{ "title": "文档2", "passage": "测试内容4"}


# 方式2，根据query筛选后应用script执行命令进行替换, **中文不一定支持**
curl -XPOST "${es_host}/book_index/_update_by_query" -H 'Content-Type: application/json' -d'
{
  "query": {
    "prefix": { "passage": "测试" }
  },
  "script": {
    "source": "ctx._source.passage = '132'"
  }
}'


# 计数
curl -XGET "${es_host}/book_index/_count" -H 'Content-Type: application/json' -d'
{
  "query": { "term": { "passage.keyword": "测试内容1" } }
}'
```


5. 替换 vs 更新


| **特性**               | **更新（Update）**                                                                 | **替换（Replace）**                                                                 |
|------------------------|------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **操作类型**           | 部分修改（仅更新指定字段）                                                         | 全量覆盖（替换整个文档）                                                           |
| **API 方法**           | `POST /index/_update/{id}`                                                         | `PUT /index/_doc/{id}`                                                             |
| **对原文档的影响**     | 保留未修改的字段                                                                   | 未包含的字段会被删除                                                               |
| **性能开销**           | 较低（仅修改差异部分）                                                             | 较高（需重建整个文档）                                                             |
| **适用场景**           | - 修改少量字段<br>- 保留其他字段                                                   | - 文档结构大幅变更<br>- 需要完全覆盖旧数据                                         |



#### 检索


1. 检索方式对比
  - 基于上文创建的 **articles** index来实现检索


| 对比维度         | Term-level Queries                                | Full-Text Queries（如 `match`、`query_string`）      |
|------------------|---------------------------------------------------|-----------------------------------------------------|
| 适用字段         | `keyword`、数值、日期、布尔等未分词字段            | `text` 类型字段（分词字段）                          |
| 查询处理方式     | 直接匹配索引中的原始值（不分析查询词）              | 对查询词分词后匹配分词结果（如 "Hello World" 拆分为 "hello" 和 "world"） |
| 大小写敏感       | 严格敏感（需完全一致，如 "Apple"≠"apple"）          | 通常不敏感（取决于分词器，如默认转为小写）            |
| 相关性评分       | 无评分（仅过滤，`_score` 固定为 0 或 1）            | 有相关性评分（`_score` 动态计算，用于结果排序）       |
| 典型用途         | 精确匹配、范围过滤、状态筛选（结构化数据）           | 全文搜索、模糊匹配、语义分析（非结构化文本）          |
| 性能特点         | 极快（直接定位倒排索引）                            | 较慢（需计算相关性得分，处理分词逻辑）                |
| 示例场景         | 订单号匹配、价格区间过滤、标签筛选                  | 文章内容搜索、商品描述模糊查询                        |
| 典型查询类型     | `term`、`terms`、`range`、`exists`、`prefix`       | `match`、`multi_match`、`match_phrase`               |
| 特殊字符处理     | 需严格匹配（如 `C++` 需原样保留）                   | 可能被分词器忽略或处理（如标点符号）                  |



2. 精确匹配
    - 检索 publisher 为 addison-wesley的结果
    - 多条件精确匹配 publisher 为 addison-wesley 且 num_reviews大于30 且 前缀为 Pro 的结果

```sh
# 检索 publisher 为 addison-wesley的结果
{
  "query": {
    "term": {
      "title.keyword": "文档2"
    }
  },
  "size": 100,
  "from": 0,
  "sort": []
}
```


```sh
# 根据文档ID进行检索
{
  "query": {
    "query_string": {
      "query": "_id:1001"
    }
  },
  "size": 10,
  "from": 0,
  "sort": []
}
```



```sh
# 多条件精确匹配 publisher 为 addison-wesley 且 num_reviews大于30 且 前缀为 Pro 的结
{
  "query": {
    "bool": {
      "must": [  // and拼接条件
        { "term": { "publisher.keyword": "addison-wesley" } },
        { "prefix": { "title": "pro" } },
        { "range": { "num_reviews": {"gte": 15} } }
      ]
    }
  },
  "size": 100,
  "from": 0,
  "sort": []
}
```


3. 多条件检索


```sh
{
  "query": {
    "bool": {
      "must": [
        { "query_string": { "query": "*" } }
      ],
      "filter": [
        { "term": { "title.keyword": "文档2" } }
      ]
    }
  },
  "size": 100,
  "from": 0,
  "sort": []
}
```


4. 模糊搜索
    - 对title字段模糊匹配pyvascript


```sh
{
  "query": {
    "fuzzy": {"title": {"value": "pyvascript"}}
  },
  "size": 100,
  "from": 0,
  "sort": []
}
```



5. bool逻辑组合匹配查询
    - 组合查询， must + must not组合查询


```sh
{
  "query": {
    "bool": {
        "must": [{"match": {"title": "javascript"}}],
        "must_not": [{"range": {"num_reviews": {"lte": 45}}}]
        }
  },
  "size": 100,
  "from": 0,
  "sort": []
}
```


#### 删除数据


1. 删除单条数据
    - 直接通过vue工具搜索出结果后，选中删除
    - 通过curl调用接口


```sh
curl -X DELETE "${es_host}/{索引名}/_doc/{文档ID}"
```


2. 批量删除
    - 删除满足条件的所有数据
    - 直接通过vue工具搜索出结果后，选中删除
    - 通过curl调用接口


```sh
# 方式1：根据条件删除
curl -X POST "${es_host}/book_index/_delete_by_query?wait_for_completion=false" -H 'Content-Type: application/json' -d'
{
  "query": {
    "fuzzy": {"title": {"value": "pyvascript"}}
  }
}'
curl -X GET "${es_host}/_tasks/<task_id>"


# 方式3：显示传参

vim bulk_delete.json
{"delete": {"_index": "book_index", "_id": "1001"}}
{"delete": {"_index": "book_index", "_id": "4ddh6JYBB66JPEoPYro4"}}

curl -X POST "${es_host}/_bulk" -H 'Content-Type: application/json' --data-binary "@bulk_delete.json"
```




#### 其他命令

| **操作名称**               | **功能**                                                                 | **典型使用场景**                                                                 | **注意事项**                                                                 | **常见命令/API**                                                                 |
|---------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **合并索引（Force Merge）** | 将多个小段（segment）合并为更少的大段，减少文件数量并释放磁盘空间。                    | - 优化查询性能<br>- 减少磁盘占用<br>- 索引不再写入后清理碎片                                  | - 高 I/O 和 CPU 消耗<br>- 合并后无法回滚<br>- 避免在写入频繁时操作           | `POST /index/_forcemerge?max_num_segments=1`                                    |
| **重建索引（Reindex）**    | 将数据从旧索引复制到新索引，支持修改映射（mapping）、分片策略或过滤数据。               | - 修改字段类型<br>- 调整分片数量<br>- 数据迁移或版本升级                                      | - 数据量大时耗时<br>- 需监控任务状态<br>- 可能需关闭旧索引写入               | `POST _reindex { "source": { "index": "old_index" }, "dest": { "index": "new_index" } }` |
| **别名（Alias）**          | 为索引绑定逻辑名称，支持无缝切换索引或跨索引查询。                                     | - 灰度发布（零停机切换索引）<br>- 联合查询多个索引<br>- 隐藏真实索引名增强灵活性               | - 别名无存储开销<br>- 可绑定多个索引<br>- 查询时自动路由                     | `PUT /index/_alias/alias_name`<br>或通过 Kibana 界面操作                        |
| **刷新索引（Refresh）**    | 强制将内存中的新数据生成可搜索的段（segment），使写入立即可见。                        | - 测试时立即验证写入结果<br>- 需要低延迟搜索的实时场景                                        | - 频繁刷新会降低写入吞吐量<br>- 默认每秒自动刷新（可调整参数）               | `POST /index/_refresh`                                                          |
| **Flush 索引（Flush）**    | 将内存缓冲区（buffer）和事务日志（translog）数据写入磁盘，确保数据持久化并清空 translog。 | - 计划关闭索引前<br>- 定期持久化数据防丢失<br>- 恢复索引前准备                                | - 不影响搜索性能<br>- 频繁 Flush 增加磁盘 I/O<br>- translog 默认异步持久化   | `POST /index/_flush`                                                            |




### python实操

- client连接

```python
from elasticsearch import Elasticsearch
import os
es_host = os.getenv("es_host")
client = Elasticsearch(hosts=[es_host])
```


#### 增查数据

1. 写数

```python
import pandas as pd
from elasticsearch import helpers
...
client = ***

def dataframe_to_bulk_actions(df):
    """批量写入到es"""
    for index, row in df.iterrows():
        yield {
            "_index": "wikipedia_vector_index",
            "_id": row["id"],
            "_source": {
                "url": row["url"],
                "content_vector": json.loads(row["content_vector"]),
                "vector_id": row["vector_id"],
            },
        }

df = pd.DataFrame(***, columns = ["id", "url", "content_vector", "vector_id"])
start = 0
end = len(df)
batch_size = 100
for batch_start in range(start, end, batch_size):
    batch_end = min(batch_start + batch_size, end)
    batch_dataframe = df.iloc[batch_start:batch_end]
    actions = dataframe_to_bulk_actions(batch_dataframe)
    helpers.bulk(client, actions)
```


2. 查询-python
    - 查询条件1，返回title包含javascript的数据
    - 筛选条件1，在1的基础上，进一步筛选 不满足 num_reviews < 45的数据
    - 返回的score，为查询条件1中计算出来的

```sh
response = client.search(
    index="book_index", 
    query={
        "bool": {
            "must": [{"match": {"title": {"query": "javascript"}}}],
            "must_not": [{"range": {"num_reviews": {"lte": 45}}}],
        }
    },
)
```


#### 删除数据


1. 根据条件删除数据


```python
# 根据条件删除数据
query = {
    "query": {
      "fuzzy": {"title": {"value": "code"}}
    }
}

response = client.delete_by_query(
    index="book_index",
    body=query,
    conflicts="proceed",
    refresh=True
)
```


2. 删除单条数据


```python
# 删除单条数据
response = client.delete(
    index="book_index",
    id="zNct3JYBB66JPEoP3bqg",
    refresh=True
)
```


3. 批量删除指定ID的文档


```python
from elasticsearch.helpers import bulk

doc_ids = ["zdct3JYBB66JPEoP3bqg", "ztct3JYBB66JPEoP3bqg"]
actions = [
    {
        "_op_type": "delete",
        "_index": "book_index",
        "_id": doc_id
    }
    for doc_id in doc_ids
]

success_count, errors = bulk(client, actions, stats_only=True)
```


#### 更新数据


| 场景                 | 推荐方法                | 优点                          |
|----------------------|-------------------------|-------------------------------|
| 单文档部分字段更新   | `es.update()`           | 简单直接                      |
| 复杂逻辑更新         | `script` 参数           | 支持计算、条件判断            |
| 按条件批量更新       | `es.update_by_query()`  | 灵活筛选文档                  |
| 高效批量更新         | `helpers.bulk()`        | 高性能，适合大规模数据        |



1. 批量更新数据
    - 更新_id：0Nct3JYBB66JPEoP3bqg的publisher信息
    - 更新_id: 0tct3JYBB66JPEoP3bqg的num_reviews信息，通过传参实现


```sh
from elasticsearch import helpers

actions = [
    {
        "_op_type": "update",      
        "_index": "book_index",
        "_id": "0Nct3JYBB66JPEoP3bqg",
        "doc": {"publisher": "oreilly test"}
    },
    {
        "_op_type": "update",
        "_index": "book_index",
        "_id": "0tct3JYBB66JPEoP3bqg",
        "script": {
            "source": "ctx._source.num_reviews += params.inc",
            "params": {"inc": 1}
        }
    }
]

success, errors = helpers.bulk(client, actions, stats_only=True)
```




2. 根据条件更新数据


```sh
query1 = {
    "range": { "num_reviews": { "gt": "20" } }
}

script = {
    "source": "ctx._source.publisher = 'oreilly test again'"
}

response = client.update_by_query(
    index="book_index",
    body={
        "query": query1,
        "script": script
    },
    refresh=True
)
```




### 环境说明


1. 系统环境说明


```sh
ubuntu1~20.04.1
NVIDIA GeForce RTX 3090 
Python 3.10.16
CUDA Version: 12.2
nvcc: 12.6
es集群: 8.8.2
docker: 20.10.14
Elasticvue 1.7.0-stable
```


2. python环境说明
    - python库版本，请看requirements_env.txt

```sh
elasticsearch==8.9.0
sentence-transformers==3.0.0
openai==1.76.0
langchain-elasticsearch==0.3.2
```



3. 目录树


```sh
|-- datas
|   |-- article.json
|   |-- book_demo.json
|   |-- data.json
|   |-- query-rules-data.json
|   |-- synonyms_data.json
|   |-- vector_database_wikipedia_articles_embedded.csv
|   `-- workplace-docs.json
|-- envs
|   `-- requirements.txt
|-- pics
|   |-- es_api_write.png
|   `-- es_datademo.png
|-- readme.md
`-- srcs
    |-- 00_quick_start.py
    |-- 01_keyword_querying_filtering.py
    |-- 02_hybrid_search.py
    |-- 03_ELSER.py
    |-- 04_multilingual.py
    |-- 05_query_rules.py
    |-- 06_synonyms_api.py
    |-- __init__.py
    |-- chatbot.py
    |-- langchain_using_own_model.py
    |-- openai_KNN_RAG.py
    `-- question_answering.py
```