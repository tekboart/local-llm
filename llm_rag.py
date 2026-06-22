import logging
logger = logging.getLogger(__name__)

from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

from utils.tekboart.nlp.rag.vectordb import (
    init_embedding_func_ollama,
    create_or_update_vector_store, retrieve_relevant_docs,
    format_retrieved_docs,
)
from utils.tekboart.nlp.utils.formatting.prompt import prompt_structure
from utils.tekboart.nlp.utils.formatting.response import response_structure

# For typing
from typing import Optional
from langchain.vectorstores.base import VectorStore
from langchain_ollama import OllamaLLM

def ask_llm(
    query: str,
    llm: OllamaLLM,
    vector_store: VectorStore,
    top_k: int,
    thresh: Optional[float] = None
) -> str:
    """
    Retrieve relevant context using a Retrieval-Augmented Generation (RAG) approach
    and generate a response using an Ollama LLM.

    Args:
        query (str): The input query to process.
        llm (OllamaLLM): The LLM instance used for generating responses.
        vector_store (VectorStore): The vector store used for document retrieval.
        top_k (int): The number of top documents to retrieve.
        thresh (Optional[float]): The similarity threshold for document retrieval. Defaults to None.

    Returns:
        str: The generated response from the LLM.
    """
    relevant_docs = retrieve_relevant_docs(query, vector_store, top_k=top_k, thresh=thresh)
    format_ = 'json'
    context = format_retrieved_docs(relevant_docs, format=format_)

    # Create the prompt, based on a pre-defined prompt structure
    prompt = prompt_structure.format(context=context, query=query, format=format_)

    with open('prompt.md', 'w') as f:
        f.write(prompt)

    response_by_rag = llm.invoke(input=prompt)

    return response_by_rag


if __name__ == "__main__":
    DATA_DIR = "./data/test"
# Set up persistent ChromaDB storage
    PERSIST_DIRECTORY = "./db/chroma_db"

    MODELS = [
        'llama3.2',
        'deepseek-r1:1.5b',
        'deepseek-r1:7b',
        'deepseek-r1:14b',
        'deepseek-r1:32b',
    ]

    print("Choose the LLM: (default (1))")
    print("Options:")
    for idx, x in enumerate(MODELS, start=1):
        print(f'({idx}) {x}')
    print()

    MODEL_NAME = MODELS[int(input("Enter the number (e.g., 1):") or "1") - 1]
    print(f'{MODEL_NAME = }')
    print(79 * "-")

    EMBEDDING_MODEL = OllamaEmbeddings

    TOP_K_SOURCE = 6
    embedding_function = init_embedding_func_ollama(EMBEDDING_MODEL, MODEL_NAME)

    TEXT_SPLIT_FUNC = {
# method 1: Splitting by fixed chunk_size (not sopphisticate)
        'recursive': RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100),
        'semantic': SemanticChunker(
            embedding_function,
            breakpoint_threshold_type="gradient",
            breakpoint_threshold_amount=95.0
        )
    }

    print(79 * "-", "\ncreating the RAG database\n", 79 * "-", sep="")
    vector_db = create_or_update_vector_store(
        data_dir=DATA_DIR,
        db_dir=PERSIST_DIRECTORY,
        embedding_func=embedding_function,
        text_split_func=TEXT_SPLIT_FUNC['recursive'],
        update=False
    )

    user_query = input("Enter your prompt:\n")

    print(79 * "-", "\nLLM Thinking ;)\n", 79 * "-", sep="")
    llm = Ollama(model=MODEL_NAME)
    response = ask_llm(
        query=user_query,
        llm=llm,
        vector_store=vector_db,
        top_k=TOP_K_SOURCE,
        thresh=0.05
    )

    print(79 * "-", "\nResponse generated with success\n", 79 * "-", sep="")

    if response:
        with open('response.md', 'w') as f:
            f.write(response_structure.format(MODEL_NAME=MODEL_NAME, prompt=user_query, response=response))
