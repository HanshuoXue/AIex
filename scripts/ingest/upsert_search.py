import os, json, sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


endpoint = os.environ["SEARCH_ENDPOINT"]
index = sys.argv[1] # e.g., "nz-faq" or "nz-programs"
client = SearchClient(endpoint=endpoint, index_name=index, credential=AzureKeyCredential(os.environ["SEARCH_KEY"]))


raw = sys.stdin.read()
try:
    docs = json.loads(raw)
    if isinstance(docs, dict):
        docs = [docs]
except json.JSONDecodeError:
    docs = [json.loads(l) for l in raw.splitlines() if l.strip()]
    
r = client.upload_documents(docs)
print({"uploaded": sum(1 for x in r if x.succeeded), "errors": [x for x in r if not x.succeeded]})