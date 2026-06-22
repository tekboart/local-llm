import os
from typing import Optional

import ollama  # Official Python client

def _ollama_has_model(model_name: str) -> bool:
    """
    Return True if `model_name` is available on the local Ollama instance.

    Uses the official Ollama Python client to query the local server.
    """
    try:
        # The official client uses the local server by default.
        # models = ollama.list()  # returns a list of dicts
        # return any(m.get("name") == model_name for m in models)
        # print(f"{models['models'][0]['model'] = }")
        # return any(m.get("name") == model_name for m in models["models"])
        response: ChatResponse = ollama.chat(model=model_name, messages=[
            {
                'role': 'user',
                'content': 'hello',
            }
        ])
        return True
    except ollama.ResponseError as e:
        print(f"[ollama_has_model] Ollama API error: {e}")
        return False
    except Exception as e:
        print(f"[ollama_has_model] Unexpected error: {e}")
        return False


def llm_chat_init(model_provider: str,
             model_name: str,
             api_key: Optional[str] = None,
             temp: float = 0.3,
             streaming: bool = True,
             auto_pull: bool = True):
    """
    Initialise an LLM stream for the requested provider/name.

    For `model_provider="ollama"`:
      • If the model is missing and `auto_pull` is True,
        the function pulls it automatically (blocking).
      • If Ollama isn't running, a RuntimeError is raised with a clear message.
    """

    if model_provider == "ollama":
        # Pull the model if it's not already here
        if auto_pull and not _ollama_has_model(model_name):
            try:
                print(f"⚠️ [llm_init] Model '{model_name}' not found locally. Pulling…")
                ollama.pull(model_name)  # This uses the native API, not subprocess
                print(f"✅ [llm_init] Successfully pulled model '{model_name}'.")
            except ollama.ResponseError as e:
                raise RuntimeError(
                    f"Failed to pull Ollama model '{model_name}': {e.message}"
                ) from None
            except Exception as e:
                raise RuntimeError(
                    f"Unexpected error while pulling Ollama model '{model_name}': {e}"
                ) from None

        from langchain_ollama import ChatOllama
        llm_stream = ChatOllama(
            model=model_name,
            temperature=temp,
            streaming=streaming,
        )

    elif model_provider == "openai":
        from langchain_openai import ChatOpenAI
        llm_stream = ChatOpenAI(
            model=model_name,
            temperature=temp,
            streaming=streaming,
            openai_api_key=api_key,
        )

    elif model_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm_stream = ChatAnthropic(
            model=model_name,
            temperature=temp,
            streaming=streaming,
            anthropic_api_key=api_key,
        )

    elif model_provider == "azure-openai":
        from langchain_openai import AzureChatOpenAI
        llm_stream = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZ_OPENAI_ENDPOINT"),
            openai_api_version="2024-02-15-preview",
            model=model_name,
            openai_api_key=os.getenv("AZ_OPENAI_API_KEY") or api_key,
            openai_api_type="azure",
            temperature=temp,
            streaming=streaming,
        )

    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {model_provider}")

    return llm_stream
