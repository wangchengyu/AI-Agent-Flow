from typing import List

def split_into_chunks(doc_file: str) -> List[str]:
    with open(doc_file, 'r') as file:
        content = file.read()

    return [chunk for chunk in content.split("\n\n")]

chunks = split_into_chunks("doc.md")

for i, chunk in enumerate(chunks):
    print(f"[{i}] {chunk}\n")


from sentence_transformers import SentenceTransformer
from safetensors import safe_open

embedding_model = SentenceTransformer("moka-ai/m3e-small") #"shibing624/text2vec-base-chinese")
print(embedding_model)

def embed_chunk(chunk: str) -> List[float]:
    embedding = embedding_model.encode(chunk, normalize_embeddings=True)
    return embedding.tolist()


embedding = embed_chunk("测试内容")
print(len(embedding))
print(embedding)

embeddings = [embed_chunk(chunk) for chunk in chunks]

print(len(embeddings))
print(embeddings[0])



import chromadb

chromadb_client = chromadb.EphemeralClient()
chromadb_collection = chromadb_client.get_or_create_collection(name="default")

def save_embeddings(chunks: List[str], embeddings: List[List[float]]) -> None:
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chromadb_collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[str(i)]
        )

save_embeddings(chunks, embeddings)

def retrieve(query: str, top_k: int) -> List[str]:
    query_embedding = embed_chunk(query)
    results = chromadb_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results['documents'][0]

query = "哆啦A梦使用的3个秘密道具分别是什么？最终战斗发生在哪里,和谁?"
retrieved_chunks = retrieve(query, 5)

for i, chunk in enumerate(retrieved_chunks):
    print(f"[{i}] {chunk}\n")

from sentence_transformers import CrossEncoder

def rerank(query: str, retrieved_chunks: List[str], top_k: int) -> List[str]:
    cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
    pairs = [(query, chunk) for chunk in retrieved_chunks]
    scores = cross_encoder.predict(pairs)

    scored_chunks = list(zip(retrieved_chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    return [chunk for chunk, _ in scored_chunks][:top_k]

reranked_chunks = rerank(query, retrieved_chunks, 3)

for i, chunk in enumerate(reranked_chunks):
    print(f"[{i}] {chunk}\n")

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

def generate(query: str, chunks: List[str]) -> str:
    prompt = f"""你是一位知识助手，请根据用户的问题和下列片段生成准确的回答。

用户问题: {query}

相关片段:
{"\n\n".join(chunks)}

请基于上述内容作答，不要编造信息。"""

    print(f"{prompt}\n\n---\n")

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat:free",
        messages=[
            {"role": "system", "content": "你是一位知识助手"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=10240
    )

    return response.choices[0].message.content

answer = generate(query, reranked_chunks)
print(answer)