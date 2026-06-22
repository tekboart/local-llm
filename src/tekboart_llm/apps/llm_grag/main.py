import os
import pytesseract
import networkx as nx
import numpy as np
from PIL import Image
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings, JinaEmbeddings,OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Set up persistent ChromaDB storage
persist_directory = "./db/chroma_db"
# MODEL_NAME = 'deepseek-r1:14b'
MODEL_NAME = 'mistral'
# EMBEDDING_MODEL = OpenAIEmbeddings
EMBEDDING_MODEL = OllamaEmbeddings
embedding_model = EMBEDDING_MODEL(model=MODEL_NAME)

# Remove any previous chroma Databases
import shutil
shutil.rmtree(persist_directory)

# Correct initialization of Chroma
vector_store = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)

def extract_text_from_image(image_path):
    """Extract text from an image using OCR."""
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

def process_files(directory):
    """Load and process files from the directory."""
    documents = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
            docs = loader.load()
        elif filename.endswith(".txt"):
            loader = TextLoader(filepath)
            docs = loader.load()
        elif filename.endswith(".md"):
            loader = UnstructuredMarkdownLoader(filepath)
            docs = loader.load()
        elif filename.endswith((".jpg", ".png")):
            text = extract_text_from_image(filepath)
            docs = [Document(page_content=text, metadata={"source": filename})]
        else:
            continue  # Skip unsupported file types

        for doc in docs:
            chunks = text_splitter.split_documents([doc])
            documents.extend(chunks)

    return documents

def calculate_similarity(doc1, doc2):
    """Calculate semantic similarity between two documents."""
    # Example: Use embeddings to calculate cosine similarity
    embedding1 = embedding_model._embed([doc1.page_content])[0]
    embedding2 = embedding_model._embed([doc2.page_content])[0]

    # Cosine similarity (adjust for actual method)
    cosine_sim = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
    return cosine_sim

def build_document_graph(documents):
    """Build a graph of documents based on semantic similarity."""
    graph = nx.Graph()

    # Add nodes (documents) to the graph
    for idx, doc in enumerate(documents):
        graph.add_node(idx, content=doc.page_content)

    # Add edges based on semantic similarity between documents
    for i in range(len(documents)):
        for j in range(i + 1, len(documents)):
            similarity_score = calculate_similarity(documents[i], documents[j])  # Define your similarity function
            if similarity_score > 0.5:  # Threshold for edge creation
                graph.add_edge(i, j, weight=similarity_score)

    return graph

def graph_based_retrieval(query, documents, graph):
    """Perform graph-based retrieval to get the most relevant documents."""
    # Get the query embedding
    query_embedding = embedding_model.embed([query])[0]

    # Calculate similarity between the query and each document node in the graph
    similarities = []
    for node in graph.nodes:
        doc_embedding = embedding_model.embed([documents[node].page_content])[0]
        cosine_sim = np.dot(query_embedding, doc_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding))
        similarities.append((node, cosine_sim))

    # Sort by similarity and return the most relevant documents
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_nodes = [node for node, _ in similarities[:3]]  # Top 3 documents

    # Retrieve the documents corresponding to the top nodes
    relevant_docs = [documents[node] for node in top_nodes]
    return relevant_docs

def ask_llm(query, documents, graph):
    """Retrieve context from Graph-based retrieval and generate response using Ollama LLM."""
    relevant_docs = graph_based_retrieval(query, documents, graph)
    context = "\n".join([doc.page_content for doc in relevant_docs])

    llm = Ollama(model=MODEL_NAME)
    prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    response = llm.invoke(prompt)
    return response

def add_to_vector_store(directory):
    """Convert documents into embeddings and store them in ChromaDB."""
    documents = process_files(directory)
    if documents:
        vector_store.add_documents(documents)

if __name__ == "__main__":
    data_directory = "./data/literature"
    add_to_vector_store(data_directory)

    # Retrieve documents from the vector store
    documents = process_files(data_directory)

    # Build the document graph
    graph = build_document_graph(documents)

    # Example user query
    user_query = "How Mahdi and Zhengnan are related?"

    # Get the response using graph-based retrieval and LLM
    response = ask_llm(user_query, documents, graph)
    print("Response:", response)

    if response:
        with open('response.md', 'w') as f:
            f.write(response)
