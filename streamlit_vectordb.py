import streamlit as st

import os
from time import time

from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    Docx2txtLoader,
)

# FIXME: This one is temporary, we should use the selected model from the UI
MODEL_NAME = "llama3.2"

from config import DB_DOCS_LIMIT

# Move the relevant codes (from streamlit_methods.py) here

from utils.tekboart.nlp.rag.vectordb import init_embedding_func_ollama

from langchain_ollama import OllamaEmbeddings
EMBEDDING_MODEL = OllamaEmbeddings

def init_embedding_func(local, embedding_model, model_name):
    """
    Initialize and return an embedding function based on the local setting.

    Args:
        local (bool): If True, use OllamaEmbeddings; otherwise, use OpenAIEmbeddings.

    Returns:
        object: Initialized embedding function.
    """
    if local:
        embedding_func =  init_embedding_func_ollama(embedding_model, model_name)
    else:
        if "AZ_OPENAI_API_KEY" not in os.environ:
            embedding_func = OpenAIEmbeddings(api_key=st.session_state.openai_api_key)
        else:
            embedding_func = AzureOpenAIEmbeddings(
                api_key=os.getenv("AZ_OPENAI_API_KEY"),
                azure_endpoint=os.getenv("AZ_OPENAI_ENDPOINT"),
                model="text-embedding-3-large",
                openai_api_version="2024-02-15-preview",
            )

    return embedding_func

def initialize_vector_db(docs, embedding_function, db_name:str):
    """
    Initialize a vector database using ChromaDB with the provided documents and embedding function.
    Args:
        docs (list): List of documents to be added to the database.
        model_name (str): Name of the model used for embedding.
        embedding_function (callable): Function to embed the documents.
        db_name (str): Name of the database collection.
        * e.g., "vectordb_user"
    Returns:
        Chroma: An instance of the Chroma vector database.
    """

    vector_db = Chroma.from_documents(
        documents=docs,
        embedding=embedding_function,
        collection_name=f"{str(time()).replace('.', '')[:14]}_" + st.session_state["session_id"],
    )

    # We need to manage the number of collections that we have in memory, we will keep the last 20
    chroma_client = vector_db._client

    # Limit the number of collections using a pre-defined limit (e.g., DB_DOCS_LIMIT)
    # collection_names = sorted(
    #     [collection.name for collection in chroma_client.list_collections()]
    # )
    # print("Number of collections:", len(collection_names))
    # while len(collection_names) > DB_DOCS_LIMIT:
    #     chroma_client.delete_collection(collection_names[0])
    #     collection_names.pop(0)

    return vector_db

def _split_and_load_docs(docs, embedding_func, db_name:str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )

    document_chunks = text_splitter.split_documents(docs)

    if st.session_state.get(db_name) is None:
        st.session_state[db_name] = initialize_vector_db(docs, embedding_func, db_name=db_name)
    else:
        st.session_state[db_name].add_documents(document_chunks)

# TODO: Make a wrapper/decorator for streamlit function (e.g., for using st.toast for error/success messages)
# So just use function from utils/archamnu_llm/rag/loader.py
# FIXME: Update a session state (for the user uploaded files) to avoid re-uploading the same file + ability to remove/replace the files
# Therefore, this session state should always replace the user_vecdb (only if sate has changed) --> This way always current nad relevant info will be given as context
def load_doc_to_db(db_docs_limit:int, embedding_function, db_name:str):
    # Use loader according to doc type
    if "rag_docs" in st.session_state and st.session_state.rag_docs:
        documents = []
        for doc_file in st.session_state.rag_docs:
            if doc_file.name not in st.session_state.rag_sources:
                if len(st.session_state.rag_sources) < db_docs_limit:
                    os.makedirs("temp/source_files", exist_ok=True)
                    file_path = f"./temp/source_files/{doc_file.name}"
                    with open(file_path, "wb") as file:
                        file.write(doc_file.read())

                    # Method 1 (Works 100%)
                    # try:
                    #     if doc_file.type == "application/pdf":
                    #         loader = PyPDFLoader(file_path)
                    #     elif doc_file.name.endswith(".docx"):
                    #         loader = Docx2txtLoader(file_path)
                    #     elif doc_file.type in ["text/plain", "text/markdown"]:
                    #         loader = TextLoader(file_path)
                    #     else:
                    #         st.warning(f"Document type {doc_file.type} not supported.")
                    #         continue

                    #     documents.extend(loader.load())
                    #     st.session_state.rag_sources.append(doc_file.name)

                    # except Exception as e:
                    #     st.toast(
                    #         f"Error loading document {doc_file.name}: {e}", icon="⚠️"
                    #     )
                    #     print(f"Error loading document {doc_file.name}: {e}")

                    # finally:
                    #     os.remove(file_path)

                    try:
                        from utils.tekboart.nlp.rag.loader import file_loader, LOADERS
                        supported_file_types = LOADERS.keys()
                        if doc_file.name.endswith(tuple(supported_file_types)):
                            docs = file_loader(file_path, loaders=LOADERS)
                        else:
                            raise Exception(f"Unsupported file type: {doc_file.name}. Supported types are: {LOADERS.keys()}")

                        if isinstance(docs, list):
                            documents.extend(docs)
                            st.session_state.rag_sources.append(doc_file.name)
                        else:
                            st.warning(f"Document type {doc_file.type} not supported.")
                            continue

                    except Exception as e:
                        st.toast(
                            f"Error loading document {doc_file.name}: {e}", icon="⚠️"
                        )
                        print(f"Error loading document {doc_file.name}: {e}")

                    finally:
                        os.remove(file_path)

                else:
                    st.error(f"Maximum number of documents reached ({DB_DOCS_LIMIT}).")

        if documents:
            _split_and_load_docs(documents, embedding_function, db_name=db_name)
            st.toast(
                f"Document *{str([doc_file.name for doc_file in st.session_state.rag_docs])[1:-1]}* loaded successfully.",
                icon="✅",
            )


# TODO: IT's redundant with the load_file_to_db function. Try to use decorators to avoid code duplication (following the DRY principle)
def load_url_to_db(embedding_function, db_name:str, sub_pages:bool=False):
    # TODO: Use ulr_loader
    from utils.tekboart.nlp.rag.loader import url_loader

    if "rag_url" in st.session_state and st.session_state.rag_url:
        base_url = st.session_state.rag_url

        # Load base page or subpages
        try:
            docs = url_loader(base_url, sub_pages)
            if docs:
                _split_and_load_docs(docs, embedding_function, db_name)
                st.toast(
                    f"The URL *{base_url}* loaded successfully.", icon="✅"
                )
            st.session_state.rag_url = ""  # Clear the input after loading
        except Exception as e:
            st.error(f"Failed to load URL {base_url}: {e}")
            st.session_state.rag_url = ""  # Clear the input after loading
            return
    # else:
    #     st.toast("⛔ Please provide a URL to load.")
    #     st.stop()

        # from bs4 import BeautifulSoup
        # import requests
        # from urllib.parse import urlparse, urljoin

        # # Step 1: Extract all links from a webpage
        # response = requests.get(base_url)
        # soup = BeautifulSoup(response.text, "html.parser")
        # base_domain = urlparse(base_url).netloc

        # urls = [
        #     urljoin(base_url, link["href"])
        #     for link in soup.find_all("a", href=True)
        #     if urlparse(urljoin(base_url, link["href"])).netloc == base_domain
        # ]

        # docs = []
        # if urls not in st.session_state.rag_sources:
        #     if len(st.session_state.rag_sources) < 10:
        #         try:
        #             loader = WebBaseLoader(urls)
        #             docs.extend(loader.load())
        #             st.session_state.rag_sources.append(urls)

        #         except Exception as e:
        #             st.error(f"Error loading document from {urls}: {e}")

        #         if docs:
        #             _split_and_load_docs(docs, embedding_function, db_name)
        #             st.toast(
        #                 f"Document from URL *{urls}* loaded successfully.", icon="✅"
        #             )

        #     else:
        #         st.error("Maximum number of documents reached (10).")