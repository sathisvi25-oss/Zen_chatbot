import os
import faiss
import ollama
import pickle
import numpy as np

from sentence_transformers import SentenceTransformer

# ==================================
# Configuration
# ==================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

FAISS_INDEX_FILE = "database/faiss_index.bin"
DOCUMENTS_FILE = "database/documents.pkl"

TOP_K = 30
MAX_CONTEXT_LENGTH = 12000

# ==================================
# Load Model
# ==================================

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

# ==================================
# Load KB
# ==================================

def load_knowledge_base():

    if (
        not os.path.exists(FAISS_INDEX_FILE)
        or
        not os.path.exists(DOCUMENTS_FILE)
    ):
        return None, [], []

    index = faiss.read_index(
        FAISS_INDEX_FILE
    )

    with open(
        DOCUMENTS_FILE,
        "rb"
    ) as f:

        data = pickle.load(f)

    return (
        index,
        data["documents"],
        data["sources"]
    )

# ==================================
# Retrieve Context
# ==================================

def retrieve_context(
    query,
    top_k=TOP_K
):

    (
        index,
        documents,
        sources
    ) = load_knowledge_base()

    if index is None:
        return "", []

    query_embedding = (
        embedding_model.encode(
            [query],
            normalize_embeddings=True
        )
    )

    query_embedding = np.array(
        query_embedding,
        dtype=np.float32
    )

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    retrieved_chunks = []
    retrieved_sources = []

    for idx in indices[0]:

        if (
            idx >= 0
            and
            idx < len(documents)
        ):

            retrieved_chunks.append(
                documents[idx]
            )

            retrieved_sources.append(
                sources[idx]
            )

    context = "\n\n".join(
        retrieved_chunks
    )

    return (
        context,
        retrieved_sources
    )

# ==================================
# Context Validation
# ==================================

def answer_exists_in_context(
    question,
    context
):

    question_words = [

        word.lower()

        for word in question.split()

        if len(word) > 3

    ]

    context_lower = context.lower()

    matches = 0

    for word in question_words:

        if word in context_lower:

            matches += 1

    return matches >= 1

# ==================================
# Ask RAG
# ==================================

def ask_rag(
    question,
    return_context=False
):

    question_lower = question.lower()

    # Company Queries

    if (
        "company" in question_lower
        or "about us" in question_lower
        or "about company" in question_lower
        or "company details" in question_lower
        or "tell me about" in question_lower
    ):

        search_query = """
        ZenFuture Technologies
        company profile
        about us
        services
        products
        mission
        vision
        """

    else:

        search_query = question

    (
        context,
        retrieved_sources
    ) = retrieve_context(
        search_query
    )

    # No Context

    if not context.strip():

        answer = (
            "I couldn't find that information "
            "in the company knowledge base."
        )

        if return_context:

            return (
                answer,
                "",
                []
            )

        return answer

    # Validate Question Exists

    if not answer_exists_in_context(
        question,
        context
    ):

        answer = (
            "I couldn't find that information "
            "in the company knowledge base."
        )

        if return_context:

            return (
                answer,
                context,
                retrieved_sources
            )

        return answer

    context = context[
        :MAX_CONTEXT_LENGTH
    ]

    prompt = f"""
You are a retrieval-only assistant.

IMPORTANT:

Use ONLY the information inside CONTEXT.

Do NOT use external knowledge.

Do NOT use training knowledge.

If the answer is not explicitly written
inside CONTEXT, reply exactly:

I couldn't find that information in the company knowledge base.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    try:

        response = ollama.chat(
            model="qwen2.5:3b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0,
                "num_predict": 300
            }
        )

        answer = response[
            "message"
        ][
            "content"
        ]

    except Exception as e:

        answer = (
            f"Error communicating with Ollama: {e}"
        )

    if return_context:

        return (
            answer,
            context,
            retrieved_sources
        )

    return answer

# ==================================
# Test
# ==================================

if __name__ == "__main__":

    while True:

        question = input(
            "\nAsk: "
        )

        if question.lower() == "exit":
            break

        (
            answer,
            context,
            sources
        ) = ask_rag(
            question,
            return_context=True
        )

        print(
            "\nSources:",
            list(set(sources))
        )

        print(
            "\nAnswer:\n",
            answer
        )