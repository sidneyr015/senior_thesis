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

reader = PdfReader("english_essay.pdf")

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

query = "physical domination"

# Step 1: Embed query
query_embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input=query
).data[0].embedding

# Step 2: Query Pinecone
results = index.query(
    vector=query_embedding,
    top_k=3,
    include_metadata=True
)

# Get the most relevant chunk and its page
main_hit = results["matches"][0]
page = main_hit["metadata"]["page"]

# Step 3: Retrieve context from nearby pages
context_results = index.query(
    vector=query_embedding,
    filter={"page": {"$in": [page - 1, page, page + 1]}},
    top_k=10,
    include_metadata=True
)

for match in context_results["matches"]:
    text = match["metadata"]["text"].replace("\n", " ")
    print(f"Page {match['metadata']['page']}: {text[:200]}...")
    #print(f"Page {match['metadata']['page']}: {match['metadata']['text'][:30]}...")