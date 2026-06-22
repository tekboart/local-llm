# see this as an example for config.py: https://github.com/LearningCircuit/local-deep-research?tab=readme-ov-file#configuration

import logging

logger = logging.getLogger(__name__)

import os

# General configuration
APP_NAME = "TekBoArt LLM"
DEBUG = True
ALLOW_CUSTOM_HTML = True  # allow HTML or just use streamlit pre-defined components

# Database configuration
DB_DOCS_LIMIT = 10

# Directory configuration
HOME_PATH = os.path.expanduser("~")
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_PATH, "data")
IMG_DIR = os.path.join(ROOT_PATH, "images")
LOG_PATH = os.path.join(ROOT_PATH, "logs")

# Logging configuration
LOG_LEVEL_CONSOLE = "INFO"
LOG_LEVEL_FILE = "DEBUG"
LOG_VERBOSITY = "verbose"  # 'default', 'verbose', 'clean'

from datetime import datetime, timedelta
from time import time

time_format = "%Y.%m.%d@%H-%M-%S"
timestamp_main = datetime.today().strftime(time_format)
LOG_FILE_PATH = os.path.join(LOG_PATH, f"{timestamp_main}.log")

# NOTE: Get the sensitive information from the environment variables, hence no hardcoding.
# NOTE: Set the default values for the environment variables in the .env file.
# Then use .env here using dotenv and os.getenv
from dotenv import load_dotenv

# Load .env variables into environment
# NOTE: Used "ovverride=True" to get the newest values from the .env file (good for test/dev)
load_dotenv(override=True)

# Database configuration
# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_PORT = int(os.getenv("DB_PORT", 5432))
# DB_USER = os.getenv("DB_USER", "user")
# DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
# DB_NAME = os.getenv("DB_NAME", "mydatabase")

# temp directory for storing files
TEMP_UPLOAD_DIR = os.path.join(ROOT_PATH, "temp", "chat_uploads")
if not os.path.exists(TEMP_UPLOAD_DIR):
    os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Streamlit configuration
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))


# Other settings
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

MODELS = {
    "local": {
        "Llama 3.2": "ollama/llama3.2",  # the default (i.e., 3b)
        "Gemma3": "ollama/gemma3",  # the default (i.e., 4b)
        "DeepSeek-R1": "ollama/deepseek-r1",  # the default (i.e., 7b)
        "Mistral 7b": "ollama/mistral",  # the default (i.e., 7b)
        "Mistral small-24b": "ollama/mistral-small",  # the default (i.e., 24b)
        "Phi4": "ollama/phi4",  # the default (i.e., 14b)
        "Phi4 mini": "ollama/phi4-mini",  # the default (i.e., 3.8b)
        "Qwen 2.5": "ollama/qwen2.5",  # the default (i.e., 7b)
        "Llama Code": "ollama/codellama",  # the default (i.e., 7b)
        "Gemma Code": "ollama/codegemma",  # the default (i.e., 7b)
        "DeepSeek Coder V2": "ollama/deepseek-coder-v2",  # the default (i.e., 16b)
        "Qwen Coder 2.5": "ollama/qwen2.5-coder",  # the default (i.e., 7b)
        "Mistral Code": "ollama/codestral",  # the default (i.e., 22b)
        # More options, from: https://ollama.com/models
        # -- llama (Meta)
        "Llama 3.2 (1b)": "ollama/llama3.2:1b",
        "Llama 3.2 (3b)": "ollama/llama3.2:3b",
        "Llama Code (7b)": "ollama/codellama:7b",
        "Llama Code (13b)": "ollama/codellama:13b",
        "Llama Code (34b)": "ollama/codellama:34b",
        # "Llama Code (70b)": "ollama/codellama:70b",
        # "Llama3.3": "ollama/llama3.3",  # the default (i.e., 70b) # NOTE: needs at least 36.3 GiB of RAM
        # "Llama 4": "ollama/llama4",
        # -- DeepSeek
        "DeepSeek-R1 (1.5b)": "ollama/deepseek-r1:1.5b",
        "DeepSeek-R1 (7b)": "ollama/deepseek-r1:7b",
        "DeepSeek-R1 (14b)": "ollama/deepseek-r1:14b",
        "DeepSeek-R1 (32b)": "ollama/deepseek-r1:32b",
        "DeepSeek Coder V2 (16b)": "ollama/deepseek-coder-v2:16b",
        "DeepSeek Coder V2 (236b)": "ollama/deepseek-coder-v2:236b",
        # -- Gemma (Google)
        "Gemma3 (1b)": "ollama/gemma3:1b",
        "Gemma3 (4b)": "ollama/gemma3:4b",
        "Gemma3 (12b)": "ollama/gemma3:12b",
        "Gemma3 (27b)": "ollama/gemma3:27b",
        "Gemma Code (2b)": "ollama/codegemma:2b",
        "Gemma Code (7b)": "ollama/codegemma:7b",
        # -- Qwen (Alibaba)
        "Qwen 2.5 (0.5b)": "ollama/qwen2.5:0.5b",
        "Qwen 2.5 (1.5b)": "ollama/qwen2.5:1.5b",
        "Qwen 2.5 (3b)": "ollama/qwen2.5:3b",
        "Qwen 2.5 (7b)": "ollama/qwen2.5:7b",
        "Qwen 2.5 (14b)": "ollama/qwen2.5:14b",
        "Qwen 2.5 (32b)": "ollama/qwen2.5:32b",
        "Qwen 2.5 (72b)": "ollama/qwen2.5:72b",
        "Qwen Coder 2.5 (0.5b)": "ollama/qwen2.5-coder:0.5b",
        "Qwen Coder 2.5 (1.5b)": "ollama/qwen2.5-coder:1.5b",
        "Qwen Coder 2.5 (3b)": "ollama/qwen2.5-coder:3b",
        "Qwen Coder 2.5 (7b)": "ollama/qwen2.5-coder:7b",
        "Qwen Coder 2.5 (14b)": "ollama/qwen2.5-coder:14b",
        "Qwen Coder 2.5 (32b)": "ollama/qwen2.5-coder:32b",
        "Qwen Coder 2.5 (72b)": "ollama/qwen2.5-coder:72b",
        # -- Mistral (Mistral AI)
        "Mistral (7b)": "ollama/mistral:7b",
        "Mistral small (22b)": "ollama/mistral-small:22b",
        "Mistral small (24b)": "ollama/mistral-small:24b",
        "Mistral Large (123b)": "ollama/mistral-large:123b",
        "Mistral Code (22b)": "ollama/codestral:22b",
        # -- Phi (Microsoft)
        "Phi4 (14b)": "ollama/phi4:14b",  # the default (i.e., 14b)
        "Phi4 mini (3.8b)": "ollama/phi4-mini:3.8b",
    },
    "non_local": {
        "O1-mini": "openai/o1-mini",
        "GPT-4o": "openai/gpt-4o",
        "GPT-4o-mini": "openai/gpt-4o-mini",
        "Claude-3.5-Sonnet": "anthropic/claude-3-5-sonnet-20240620",
        "GPT-4o (Azure)": "azure-openai/gpt-4o",
    },
}

# GUI configuration
PRIVACY_POLICY = """
- All the files you upload are stored in memory and are not saved.
- All the queries and answers are stored in memory and are not saved.
- No one will have access to the data you upload (e.g., ETHIC-protected interview files).
"""
