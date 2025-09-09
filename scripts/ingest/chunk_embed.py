import os, json, hashlib, re
from typing import List, Dict
from openai import OpenAI


EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    base_url=f"{os.getenv('AZURE_OPENAI_ENDPOINT')}/openai/deployments/{EMBED_MODEL}",
)


# Simple tokenizer‑agnostic chunker (by chars) for FAQs
def chunk_text(text: str, chunk_size=3000, overlap=400) -> List[str]:
    s = re.sub(r"\s+", " ", text).strip()
    chunks, i = [], 0
    while i < len(s):
        chunks.append(s[i:i+chunk_size])
        i += chunk_size - overlap
    return chunks


def embed(texts: List[str]) -> List[List[float]]:
# Azure OpenAI embeddings
    resp = client.embeddings.create(input=texts, model=EMBED_MODEL)
    return [d.embedding for d in resp.data]


def make_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()