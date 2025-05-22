from elasticsearch import Elasticsearch
import os
from sentence_transformers import SentenceTransformer

es_host = os.getenv("es_host")
model = SentenceTransformer("/home/bge-large-zh-v1.5")
client = Elasticsearch(hosts=[es_host])
print(f"es: {es_host} connected status: {client.ping()}")