import logging
from typing import Callable, Optional, Dict, Iterator
logger = logging.getLogger(__name__)

# TODO: prepend the functions, classes, and contents with "_" (only the ones that are going to be used internally in this file)

# TODO: Remove all the imports that are not used in this file (Can use Copilot Edits)
import os
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import JinaEmbeddings, OpenAIEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredXMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredImageLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    WebBaseLoader,
)

# from langchain_community.vectorstores import Chroma
# give more option than langchain_community's counterpart
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

from langchain.schema import Document

# TODO: Remove as it was used in the load method of my custom PyIMageLoader class
# def _image_to_doc(file_path: str) -> list[Document]:
#     image = Image.open(file_path)
#     text = pytesseract.image_to_string(image)
#     return [Document(page_content=text, metadata={"source": file_path})]

from langchain.document_loaders.base import BaseLoader
from abc import ABC
class PyImageLoader(BaseLoader):
    """
    Custom loader (based on langchain's PyPDFLoader) for images using PyTesseract.
    """
    def __init__(
        self,
        file_path: str,
        headers: Optional[Dict] = None,
    ) -> None:
        """Initialize with a file path."""
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            import pytesseract
        except ImportError as e:
            raise ImportError(
                "PIL and pytesseract are required for PyImageLoader. Please install them using `pip install pillow pytesseract`."
            ) from e
        self.file_path = file_path
        # super().__init__(file_path, headers=headers)
        # self.parser = PyPDFParser(
        #     password=password,
        #     extract_images=extract_images,
        #     extraction_mode=extraction_mode,
        #     extraction_kwargs=extraction_kwargs,
        # )

    def load(self) -> list[Document]:
        """Load the image and extract text."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        else:
            from PIL import Image, ImageEnhance, ImageFilter
            import pytesseract
            logger.info(f"Loading image from {self.file_path}")
            # Use PyTesseract to extract text from the image
            image = Image.open(self.file_path).convert("L")  # Convert to grayscale
            image = image.filter(ImageFilter.MedianFilter())  # Remove noise
            image = ImageEnhance.Contrast(image).enhance(2)  # Enhance contrast
            # lang="eng" for English, "deu" for German, or "eng+deu" for both
            text = pytesseract.image_to_string(image, lang="eng", config=r"--oem 3 --psm 6")
            # XXX: output words boxes for visual inspection
            boxes = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            # print(boxes)
            return [Document(page_content=text, metadata={"source": self.file_path})]

    # def lazy_load(
    #     self,
    # ) -> Iterator[Document]:
    #     """Lazy load given path as pages."""
    #     if self.web_path:
    #         blob = Blob.from_data(open(self.file_path, "rb").read(), path=self.web_path)  # type: ignore[attr-defined]
    #     else:
    #         blob = Blob.from_path(self.file_path)  # type: ignore[attr-defined]
    #     yield from self.parser.parse(blob)

# --- CONSTANTS ---
# TODO: Add support for coding files: e.g., .py, .ipynb, etc.
LOADERS = {
    '.pdf': {'loader': PyPDFLoader, 'kwargs': {'password': None, 'extract_images': False}},  # TODO: enable image extraction (from PDFs) using Agentic Document Extraction (ADE)
    '.docx': {'loader': Docx2txtLoader, 'kwargs': {}},
    '.pptx': {'loader': UnstructuredPowerPointLoader, 'kwargs': {}},
    '.xlsx': {'loader': UnstructuredExcelLoader, 'kwargs': {}},
    '.csv': {'loader': CSVLoader, 'kwargs': {}},
    '.txt': {'loader': TextLoader, 'kwargs': {}},
    # TODO: Find a way to first detect the structure of the json file (is the outer delimiter a dict or a list) then use the proper 'jq_schema' accordingly.
    # case 1: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    # case 2: {"name": "Alice", "age": 30}
    # '.json': {'loader': JSONLoader, 'kwargs': {'jq_schema': '.[] | {name: .name}'}},
    # '.xml': {'loader': UnstructuredXMLLoader, 'kwargs': {}},
    '.md': {'loader': UnstructuredMarkdownLoader, 'kwargs': {}},  # FIXME: maybe I can use TextLoader instead
    # '.jpg': UnstructuredImageLoader,
    # '.png': UnstructuredImageLoader,
    # '.webp': UnstructuredImageLoader,
    '.jpg': {'loader': PyImageLoader, 'kwargs': {}},
    '.jpeg': {'loader': PyImageLoader, 'kwargs': {}},
    '.png': {'loader': PyImageLoader, 'kwargs': {}},
    '.webp': {'loader': PyImageLoader, 'kwargs': {}},
}

def extract_url_from_url_file(file_path):
    """
    Extracts the URL from a ".url" file.

    This function reads a file line by line and looks for a line that starts
    with "URL=". Once found, it extracts and returns the URL value.

    Args:
        file_path (str): The path to the ".url" file.

    Returns:
        str: The extracted URL. Returns an empty string if no URL is found.
    """
    url = ""
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('URL='):
                url = line.strip().split('=', 1)[1]
                break
    return url

def url_loader(url, sub_pages=False):
    """
    get the content of the url (to be used with a vectorDB)
    """
    if sub_pages:
        # Step 1: Extract all pages from a webpage
        from bs4 import BeautifulSoup
        import requests
        from urllib.parse import urlparse, urljoin

        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        base_domain = urlparse(url).netloc

        urls = [
            urljoin(url, link["href"])
            for link in soup.find_all("a", href=True)
            if urlparse(urljoin(url, link["href"])).netloc == base_domain
        ]

        loader = WebBaseLoader(urls)
        loader.requests_per_second = 1
        docs = loader.aload()
    else:
        loader = WebBaseLoader(url)
        docs = loader.load()

    for doc in docs:
        # add the page number to the metadata (to be consistent with the metadata of files, e.g., PDFs)
        doc.metadata['page'] = doc.metadata['title']

    # Make sure the documents are in the correct format
    from langchain_core.documents import Document  # adjust import if needed
    if isinstance(docs, list) and all(isinstance(d, Document) for d in docs):
        logger.info(f"Loaded {len(docs)} documents from {url}")
        return docs
    else:
        raise ValueError(f"Unsuccessful loading of {url}. Please check the URL or the network connection.")

def file_loader(file_path:str, loaders:dict=LOADERS):
    """
    supported files:
        documents: ".pdf", ".docx", ".txt", ".md",
        semi-structured: ".csv", ".json", ".xml"
        images: ".jpg", ".png", ".jpeg"
    """

    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        kwargs = loaders[file_ext].get("kwargs", {})
        loader = loaders[file_ext].get("loader")(file_path, **kwargs)
        docs = loader.load()  # a list of [???]
        logger.info(f"Loaded {len(docs)} documents from {file_path}")
        return docs
    except KeyError as e:
        logger.warning(f"File type {file_ext} not supported.")
        raise KeyError(f"File type {file_ext} not supported.") from e
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        raise ValueError(f"Error loading file {file_path}: {e}") from e
    finally:
        logger.info(f"File loaded successfully: {file_path}")

# TODO: make it compatible with single files (define another function and call it here in a loop for directory)
def dir_loader(
    directory,
    loaders:dict=LOADERS,
):
    """Load and process files from the directory."""
    documents = []

    # Slog through the dir hirearchy to find and load relevant files

    supported_file_types = LOADERS.keys()

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in supported_file_types:
            docs = file_loader(file_path)
        elif file_ext == '.url':
            url = extract_url_from_url_file(file_path)
            docs = url_loader(url, sub_pages=True)
        else:
            raise Exception(
                f"Unsupported file type: {filename}. Supported types are: {supported_file_types}"
            )

        assert isinstance(docs, list), f"Expected a list of documents, got {type(docs)}"
        documents += docs

    if documents:
        return documents
    else:
        raise Exception(
            f"Now document for RAG is provided. Please add at least one document (with supported file format, e.g., .pdf) to the {directory}")



def chunk_documents(
    documents: list[Document],
    text_split_func: Callable,  # e.g., RecursiveCharacterTextSplitter or SemanticChunker
):
    for doc in documents:
        # TODO: How can we still keep record of which chuncks belong to the same document?
        # TODO: Add metadata to our chunks (e.g., original_data_id, ...)--too keep track of data after chunking
        # use doc.metadata.get("page_number")
        doc.page_content = " ".join(doc.page_content.split())  # remove white space

    chunks = text_split_func.split_documents(documents)
    return chunks
