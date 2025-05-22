
"""同义词检索-nook

1. 定义具有相同或相似含义的术语之间的关系， 支持 **扩展搜索召回率**
2. 当前es版本，不支持啦
3. 具体代码，可参考 [06-synonyms-api.ipynb](https://github.com/elastic/elasticsearch-labs/blob/main/notebooks/search/06-synonyms-api.ipynb)
"""

from __init__ import client
import json


synonyms_set = [{"id": "synonym-1", "synonyms": "js, javascript, java script"}]
client.synonyms.put_synonym(id="my-synonyms-set", synonyms_set=synonyms_set)
