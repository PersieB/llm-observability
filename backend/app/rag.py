from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai
from app.database import SessionLocal
from app.models import DocumentChunk
load_dotenv()
client = genai.Client(api_key=os.environ.get("GENAI_API_KEY"))
import time

DOCUMENTS_DIR = Path("documents")


def load_documents():
    documents = []

    for file_path in DOCUMENTS_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        documents.append({
            "source": file_path.name,
            "text": text,
        })

    return documents


def chunk_text(text, chunk_size=500):
    chunks = []

    for start in range(0, len(text), chunk_size):
        chunk = text[start:start + chunk_size]
        chunks.append(chunk)

    return chunks



def create_embedding(text):
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )

    return response.embeddings[0].values


def search_similar_chunks(question, top_k=3):
    retrieval_start = time.perf_counter()

    try:
        embedding_start = time.perf_counter()

        question_embedding = create_embedding(question)

        embedding_latency = time.perf_counter() - embedding_start

    except Exception as e:
        raise RuntimeError(f"embedding: {e}")

    try:
        db_start = time.perf_counter()

        db = SessionLocal()

        results = (
            db.query(DocumentChunk)
            .order_by(
                DocumentChunk.embedding.cosine_distance(question_embedding)
            )
            .limit(top_k)
            .all()
        )

        db.close()

        vector_search_latency = time.perf_counter() - db_start

    except Exception as e:
        raise RuntimeError(f"vector_search: {e}")

    retrieval_latency = time.perf_counter() - retrieval_start

    return (
        results,
        retrieval_latency,
        embedding_latency,
        vector_search_latency,
    )



def generate_rag_answer(question, top_k=3):
    results, retrieval_latency, embedding_latency, vector_search_latency = search_similar_chunks(question, top_k)

    context = "\n\n".join(
        result.text
        for result in results
    )

    prompt = f"""
    Use the following context to answer the question.

    Context:
    {context}

    Question:
    {question}

    Answer based only on the provided context.
    """
    start_time = time.perf_counter()

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )
    except Exception as e:
        raise RuntimeError(f"llm: {e}")

    latency = time.perf_counter() - start_time
    return {
        "answer": response.text,
        "retrieved_chunks": results,
        "retrieval_latency": retrieval_latency,
        "embedding_latency": embedding_latency,
        "vector_search_latency": vector_search_latency,
        "latency": latency,
        "input_tokens": response.usage_metadata.prompt_token_count,
        "output_tokens": response.usage_metadata.candidates_token_count,
        "thought_tokens": response.usage_metadata.thoughts_token_count,
        "total_tokens": response.usage_metadata.total_token_count,
    }


def prepare_chunks():
    db = SessionLocal()

    documents = load_documents()

    for document in documents:
        text_chunks = chunk_text(document["text"])

        for chunk in text_chunks:
            embedding = create_embedding(chunk)
            document_chunk = DocumentChunk(
                source=document["source"],
                text=chunk,
                embedding=embedding,
            )
            db.add(document_chunk)
    db.commit()
    db.close()
    print("Document chunks prepared and stored in the database.")


if __name__ == "__main__":
    result = generate_rag_answer(
        "What is retrieval augmented generation?"
    )

    print("Answer:")
    print(result["answer"])

    print("\nRetrieved chunks:")
    for chunk in result["retrieved_chunks"]:
        print("---")
        print(chunk.text)