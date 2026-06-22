import logging
logger = logging.getLogger(__name__)

# TODO: prepend the functions, classes, and contents with "_" (only the ones that are going to be used internally in this file)

# TODO: Remove all the imports that are not used in this file (Can use Copilot)
import os
from time import time
import pytesseract
import chromadb
from PIL import Image
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import JinaEmbeddings, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, UnstructuredImageLoader
# from langchain_community.vectorstores import Chroma
# give more option than langchain_community's counterpart
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

def init_embedding_func_ollama(embedding_model, foundation_model: str):
    """
    Initialize and return an embedding function using the specified model.

    Args:
        embedding_model (callable): Embedding model class or function.
            e.g., OllamaEmbeddings
        foundation_model (str): Name of the foundation model.
            e.g., "llama3.1", "llama3.2", "gemini-1.5-flash", etc.

    Returns:
        object: Initialized embedding function.
    """
    embedding_func = embedding_model(model=foundation_model)
    return embedding_func

from .loader import dir_loader

def chromadb_init(docs, embedding_func, collection_name=f"{str(time()).replace('.', '')[:14]}_"):
    """
    Initialize a ChromaDB instance.

    Args:
        docs (list): List of documents to be added to the database.
        embedding_func (callable): Function to embed the documents.
        collection_name (str): Name of the collection in the database.

    Returns:
        chromadb: An instance of ChromaDB.
    """
    vector_db = Chroma.from_documents(
    documents=docs,
    embedding=embedding_func,
    collection_name=collection_name
    )

def chromadb_add_vector(chromadb, vector_id):
    """
    Adds a vector to the database.

    Args:
        # TODO: Check the type (dict???)
        chromadb (dict): The database.
        vector (list): The vector to add.
    """
    # chromadb['vectors'].append(vector)
    pass


def chromadb_remove_vector(chromadb, vector_id):
    """
    Remove files (all their chunks) from the vector database.
    """
    # FIXME: Remeber to remove the "rag_sources" from the vector DB (if the user deletes/deselects the file in future queries)
    pass

def create_or_update_vector_store(
    data_dir: str,
    db_dir: str,
    #  foundation_model: str,
    #  embedding_model,
    embedding_func,
    text_split_func,
    update: bool = True
):
    """Convert documents into embeddings and store them in ChromaDB."""
    _documents = dir_loader(data_dir)
    from .loader import chunk_documents
    documents = chunk_documents(_documents, text_split_func)
    if documents:
        embed_func = embedding_func
        if update:
            db = Chroma(
                persist_directory=db_dir,
                embedding_function=embed_func,
                # create_collection_if_not_exists=False
            )
            db.add_documents(documents)
        else:
            # # Removes any previous chroma Databases (So we don't end up with with a pre-existent DB that was created with another model--which can cause vector shape mismatch)
            if os.path.exists(db_dir):
                import shutil
                shutil.rmtree('./db')
                #  shutil.rmtree(os.path.join( os.cwd(), 'projects', 'CRCP-LLM', 'db'))
                print(f"---------- remove {db_dir} --------------")
                # shutil.rmtree("./db")
            db = Chroma.from_documents(
                documents, embedding=embed_func, persist_directory=db_dir)

        return db
    else:
        raise Exception(
            f"Now document for RAG is provided. Please add at least one document (with supported file format, e.g., .pdf) to the {DATA_DIR}")


def retrieve_relevant_docs(query, vector_store, top_k=3, thresh:int=None):
    """
    Retrieve relevant documents for a given query (only for ChromaDB).

    thresh: int = None
        score_threshold: Optional, a floating point value between 0 to 1 to filter the resulting set of retrieved docs
    """
    # retireve the relevant documents from our vectorDB, based on Cosine Similarity
    # relevant_docs = vector_store.similarity_search_with_score(query, k=top_k)
    if thresh:
        relevant_docs = vector_store.similarity_search_with_relevance_scores(query, k=top_k, score_threshold=thresh)
    else:
        relevant_docs = vector_store.similarity_search_with_relevance_scores(query, k=top_k)


    # sort the retrieved documents based on the score
    # TODO: Check if it's already sorted, then remove the sorting step
    relevant_docs.sort(key=lambda x: x[1])

    # Filter results to include only highly relevant documents
    # if thresh:
    #     relevant_docs = [(doc, scores) for doc, score in relevant_docs if score < thresh]

    return relevant_docs

def format_retrieved_docs(docs_with_scores:list[tuple], format:str='json') -> str:
    '''
    format and joint the retrieved relevant chunks of data (from a VectorDB)

    format: str = json|text
        json:
            pros:
                - Clear structure, easy to parse
                - Useful for models that handle structured data well
                - Can include multiple fields
            cons:
                - Might be too rigid for some LLMs if they expect natural text
        text:
            pros:
                - Very simple, works with most LLMs
                - No complex formatting needed
            cons:
                - Might be too rigid for some LLMs if they expect natural text
                - Harder to separate different sources if many documents are included
    '''

    if format == 'text':
        start = "- "
        # seperator = "\n\n"
        seperator = "\n- "

        # Method 1: Just the text
        # context = seperator.join([d.page_content for d in docs])

        # Method 2: Include metadata
        # print(f"{docs[0].metadata = }")
        context = seperator.join([f"('Relevancy Score: {score:.3f}', 'Source: {doc.metadata['source']}', 'Page: {doc.metadata['page']}') {doc.page_content}" for doc, score in docs_with_scores])
        formatted_context = start + context
    elif format == 'json':
        context_dict = [
            {
                'source': doc.metadata['source'],
                'page': doc.metadata.get('page'),
                'relevancy_score': round(score, 3),
                'content': doc.page_content,
            }
            for doc, score in docs_with_scores
        ]
        del docs_with_scores

        import json
        formatted_context = json.dumps(context_dict, indent=4, separators=(", ", ": "))
    else:
        raise ValueError(f"Unsupported format: {format}. Supported formats are: 'text' and 'json'.")

    return formatted_context

if __name__ == '__main__':
    logger.info(f'The {__file__} is being run as the main module.')