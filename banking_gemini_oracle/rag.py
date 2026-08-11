from pathlib import Path

from langchain_chroma import Chroma

from langchain_community.document_loaders import (
    PyPDFLoader
)

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

import config


class BankingRAG:

    def __init__(self):

        # ----------------------------------------------------
        # Create required directories
        # ----------------------------------------------------

        config.DOCUMENTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        config.CHROMA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # ----------------------------------------------------
        # Gemini Embeddings
        # ----------------------------------------------------

        self.embeddings = (
            GoogleGenerativeAIEmbeddings(

                model=config.GEMINI_EMBEDDING_MODEL,

                google_api_key=config.GOOGLE_API_KEY
            )
        )

        # ----------------------------------------------------
        # Chroma Vector Database
        # ----------------------------------------------------

        self.vectorstore = self._create_vectorstore()

    # ========================================================
    # CREATE VECTORSTORE
    # ========================================================

    def _create_vectorstore(self):

        return Chroma(

            collection_name=(
                config.CHROMA_COLLECTION
            ),

            embedding_function=(
                self.embeddings
            ),

            persist_directory=str(
                config.CHROMA_DIR
            )
        )

    # ========================================================
    # GET PDF FILES
    # ========================================================

    def get_pdf_files(self):

        pdf_files = sorted(
            config.DOCUMENTS_DIR.glob(
                "*.pdf"
            )
        )

        return pdf_files

    # ========================================================
    # LOAD PDF FILES
    # ========================================================

    def load_pdfs(self):

        documents = []

        pdf_files = self.get_pdf_files()

        print()
        print("=" * 70)
        print("BANKING RAG - PDF DISCOVERY")
        print("=" * 70)

        print(
            "PDF directory:",
            config.DOCUMENTS_DIR
        )

        print(
            "PDF count:",
            len(pdf_files)
        )

        # ----------------------------------------------------
        # No PDF
        # ----------------------------------------------------

        if not pdf_files:

            print(
                "WARNING: No PDF files found."
            )

            print(
                "Put your banking PDFs inside:"
            )

            print(
                config.DOCUMENTS_DIR
            )

            print("=" * 70)

            return []

        # ----------------------------------------------------
        # Load every PDF
        # ----------------------------------------------------

        for pdf_file in pdf_files:

            print(
                f"Loading: {pdf_file.name}"
            )

            try:

                loader = PyPDFLoader(
                    str(pdf_file)
                )

                docs = loader.load()

                print(
                    f"  Pages loaded: {len(docs)}"
                )

                for document in docs:

                    document.metadata[
                        "source"
                    ] = pdf_file.name

                    document.metadata[
                        "file_name"
                    ] = pdf_file.name

                documents.extend(
                    docs
                )

            except Exception as exc:

                print(
                    f"ERROR loading {pdf_file.name}:"
                )

                print(
                    exc
                )

        print(
            f"Total pages loaded: "
            f"{len(documents)}"
        )

        print("=" * 70)

        return documents

    # ========================================================
    # BUILD INDEX
    # ========================================================

    def build_index(self):

        print()
        print("=" * 70)
        print("BUILDING BANKING POLICY RAG INDEX")
        print("=" * 70)

        documents = self.load_pdfs()

        if not documents:

            raise RuntimeError(
                "No PDF documents were loaded. "
                f"Check: {config.DOCUMENTS_DIR}"
            )

        # ----------------------------------------------------
        # Split documents
        # ----------------------------------------------------

        splitter = (
            RecursiveCharacterTextSplitter(

                chunk_size=(
                    config.CHUNK_SIZE
                ),

                chunk_overlap=(
                    config.CHUNK_OVERLAP
                ),

                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    " ",
                    ""
                ]
            )
        )

        chunks = splitter.split_documents(
            documents
        )

        print(
            f"Created chunks: {len(chunks)}"
        )

        if not chunks:

            raise RuntimeError(
                "PDFs were loaded but "
                "no text chunks were created."
            )

        # ----------------------------------------------------
        # Delete old Chroma collection
        # ----------------------------------------------------

        try:

            self.vectorstore.delete_collection()

            print(
                "Old Chroma collection deleted."
            )

        except Exception as exc:

            print(
                "No old collection to delete."
            )

        # ----------------------------------------------------
        # Create fresh Chroma collection
        # ----------------------------------------------------

        self.vectorstore = (
            self._create_vectorstore()
        )

        # ----------------------------------------------------
        # Insert chunks
        # ----------------------------------------------------

        print(
            "Creating embeddings and "
            "storing chunks in Chroma..."
        )

        self.vectorstore.add_documents(
            chunks
        )

        # ----------------------------------------------------
        # Verify
        # ----------------------------------------------------

        count = self.get_index_count()

        print(
            f"Chroma indexed documents: "
            f"{count}"
        )

        print("=" * 70)

        return count

    # ========================================================
    # INDEX COUNT
    # ========================================================

    def get_index_count(self):

        try:

            return (
                self.vectorstore
                ._collection
                .count()
            )

        except Exception as exc:

            print(
                "Unable to get Chroma count:",
                exc
            )

            return 0

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        question,
        k=None
    ):

        if k is None:

            k = config.RAG_TOP_K

        # ----------------------------------------------------
        # Check index
        # ----------------------------------------------------

        count = self.get_index_count()

        print()
        print(
            f"RAG SEARCH: {question}"
        )

        print(
            f"Indexed chunks: {count}"
        )

        if count == 0:

            print(
                "RAG SEARCH RESULT: "
                "INDEX IS EMPTY"
            )

            return []

        # Never request more documents
        # than are actually indexed.

        k = min(
            k,
            count
        )

        try:

            documents = (
                self.vectorstore
                .similarity_search(
                    question,
                    k=k
                )
            )

            print(
                f"Documents retrieved: "
                f"{len(documents)}"
            )

            for index, document in enumerate(
                documents,
                start=1
            ):

                print(
                    f"\nResult {index}"
                )

                print(
                    "Source:",
                    document.metadata.get(
                        "source",
                        "Unknown"
                    )
                )

                print(
                    "Page:",
                    document.metadata.get(
                        "page",
                        "Unknown"
                    )
                )

                print(
                    "Text:",
                    document.page_content[
                        :300
                    ]
                )

            return documents

        except Exception as exc:

            print(
                "RAG SEARCH ERROR:"
            )

            print(
                repr(exc)
            )

            return []

    # ========================================================
    # GET CONTEXT
    # ========================================================

    def get_context(
        self,
        question
    ):

        documents = self.search(
            question
        )

        if not documents:

            return (
                "No relevant banking "
                "policy document found."
            )

        context = []

        for document in documents:

            source = (
                document.metadata.get(
                    "source",
                    "Unknown"
                )
            )

            page = (
                document.metadata.get(
                    "page",
                    "Unknown"
                )
            )

            text = (
                document.page_content
                .strip()
            )

            if not text:

                continue

            context.append(

                f"""
SOURCE: {source}
PAGE: {page}

{text}
"""
            )

        if not context:

            return (
                "No readable banking "
                "policy content found."
            )

        return "\n\n".join(
            context
        )

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        pdf_files = (
            self.get_pdf_files()
        )

        return {

            "documents_directory":
                str(
                    config.DOCUMENTS_DIR
                ),

            "pdf_count":
                len(pdf_files),

            "pdf_files": [
                pdf.name
                for pdf in pdf_files
            ],

            "indexed_chunks":
                self.get_index_count()
        }

    # ========================================================
    # TEST SEARCH
    # ========================================================

    def test_search(
        self,
        question
    ):

        print()
        print("=" * 70)
        print(
            f"TESTING RAG: {question}"
        )
        print("=" * 70)

        documents = self.search(
            question,
            k=5
        )

        if not documents:

            print(
                "NO DOCUMENTS FOUND."
            )

            return False

        print()
        print(
            f"SUCCESS: Found "
            f"{len(documents)} documents."
        )

        return True