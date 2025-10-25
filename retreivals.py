from pypdf import PdfReader
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import os

client = OpenAI() 
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

index_name = "pdf-embeddings"

if index_name not in [i["name"] for i in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=1536,  # for text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(index_name)

reader = PdfReader("rm0041.pdf")

vectors = []
for page_num, page in enumerate(reader.pages, start=1): 
    text = page.extract_text() 
    if not text: 
        continue 

    chunks = [text[i : i+1000] for i in range(0, len(text), 1000)]
    
    for chunk_idx, chunk in enumerate(chunks): 
        embedding = client.embeddings.create( 
            model="text-embedding-3-small",
            input=chunk
        ).data[0].embedding

        vectors.append({
            "id": f"page{page_num}_chunk{chunk_idx}",
            "values": embedding, 
            "metadata": {
                "page": page_num, 
                "chunk_index": chunk_idx, 
                "text": chunk
            }
        })
index.upsert(vectors=vectors)