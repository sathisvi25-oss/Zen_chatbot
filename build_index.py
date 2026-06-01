import os
import faiss
import pickle
import numpy as np

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# ==================================
# Configuration
# ==================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

WEBSITE_FILE = "data/website_content.txt"
PDF_FOLDER = "data/uploads"

FAISS_INDEX_FILE = "database/faiss_index.bin"
DOCUMENTS_FILE = "database/documents.pkl"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ==================================
# Chunk Text
# ==================================

def chunk_text(text):

    chunks = []

    start = 0

    while start < len(text):

        end = start + CHUNK_SIZE

        chunk = text[start:end]

        if chunk.strip():

            chunks.append(chunk)

        start += (
            CHUNK_SIZE -
            CHUNK_OVERLAP
        )

    return chunks


# ==================================
# Build Knowledge Base
# ==================================

def build_knowledge_base():

    print("\nLoading Embedding Model...")

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    os.makedirs(
        "database",
        exist_ok=True
    )

    # ==================================
    # Delete Old Database
    # ==================================

    if os.path.exists(
        FAISS_INDEX_FILE
    ):
        os.remove(
            FAISS_INDEX_FILE
        )

    if os.path.exists(
        DOCUMENTS_FILE
    ):
        os.remove(
            DOCUMENTS_FILE
        )

    documents = []
    sources = []

    # ==================================
    # Website Content
    # ==================================

    if os.path.exists(
        WEBSITE_FILE
    ):

        print(
            "\nReading Website Content..."
        )

        with open(
            WEBSITE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            website_text = f.read()

        website_text = " ".join(
            website_text.split()
        )

        website_chunks = chunk_text(
            website_text
        )

        for chunk in website_chunks:

            documents.append(
                f"[SOURCE: WEBSITE]\n{chunk}"
            )

            sources.append(
                "website"
            )

        print(
            f"Website Chunks: "
            f"{len(website_chunks)}"
        )

    # ==================================
    # PDF Content
    # ==================================

    if os.path.exists(
        PDF_FOLDER
    ):

        print(
            "\nReading PDFs..."
        )

        pdf_files = [

            file

            for file in os.listdir(
                PDF_FOLDER
            )

            if file.lower().endswith(
                ".pdf"
            )

        ]

        print(
            f"PDF Files Found: "
            f"{len(pdf_files)}"
        )

        for file in pdf_files:

            pdf_path = os.path.join(
                PDF_FOLDER,
                file
            )

            print(
                f"\nProcessing: {file}"
            )

            try:

                reader = PdfReader(
                    pdf_path
                )

                pdf_text = ""

                for page in reader.pages:

                    text = page.extract_text()

                    if text:

                        text = " ".join(
                            text.split()
                        )

                        pdf_text += (
                            text +
                            "\n\n"
                        )

                print(
                    f"PDF Text Length: "
                    f"{len(pdf_text)}"
                )

                if len(
                    pdf_text.strip()
                ) == 0:

                    print(
                        f"WARNING: "
                        f"{file} contains no text"
                    )

                    continue

                pdf_chunks = chunk_text(
                    pdf_text
                )

                print(
                    f"PDF Chunks: "
                    f"{len(pdf_chunks)}"
                )

                for chunk in pdf_chunks:

                    documents.append(
                        f"[SOURCE: {file}]\n{chunk}"
                    )

                    sources.append(
                        file
                    )

            except Exception as e:

                print(
                    f"Error reading "
                    f"{file}: {e}"
                )

    # ==================================
    # Remove Duplicate Chunks
    # ==================================

    print(
        "\nRemoving Duplicates..."
    )

    unique_docs = []
    seen = set()

    for doc, src in zip(
        documents,
        sources
    ):

        key = doc.strip()

        if key not in seen:

            seen.add(key)

            unique_docs.append(
                (doc, src)
            )

    documents = [
        d for d, s in unique_docs
    ]

    sources = [
        s for d, s in unique_docs
    ]

    print(
        f"Unique Chunks: "
        f"{len(documents)}"
    )

    # ==================================
    # Validation
    # ==================================

    if len(documents) == 0:

        raise ValueError(
            "No content found for indexing."
        )

    # ==================================
    # Generate Embeddings
    # ==================================

    print(
        "\nGenerating Embeddings..."
    )

    embeddings = (
        embedding_model.encode(
            documents,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
    )

    embeddings = np.array(
        embeddings,
        dtype=np.float32
    )

    # ==================================
    # Create FAISS Index
    # ==================================

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(
        embeddings
    )

    print(
        f"\nFAISS Vectors Stored: "
        f"{index.ntotal}"
    )

    # ==================================
    # Save FAISS
    # ==================================

    faiss.write_index(
        index,
        FAISS_INDEX_FILE
    )

    # ==================================
    # Save Documents
    # ==================================

    with open(
        DOCUMENTS_FILE,
        "wb"
    ) as f:

        pickle.dump(
            {
                "documents": documents,
                "sources": sources
            },
            f
        )

    # ==================================
    # Summary
    # ==================================

    website_count = 0
    pdf_count = 0

    for src in sources:

        if src == "website":
            website_count += 1
        else:
            pdf_count += 1

    print("\n====================")
    print("KNOWLEDGE BASE SUMMARY")
    print("====================")

    print(
        f"Website Chunks : "
        f"{website_count}"
    )

    print(
        f"PDF Chunks     : "
        f"{pdf_count}"
    )

    print(
        f"Total Chunks   : "
        f"{len(documents)}"
    )

    print(
        f"FAISS Vectors  : "
        f"{index.ntotal}"
    )

    print(
        "\nKnowledge Base Created Successfully"
    )

    return True


# ==================================
# Main
# ==================================

if __name__ == "__main__":

    build_knowledge_base()