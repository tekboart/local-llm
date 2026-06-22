import os
from dotenv import load_dotenv
import requests

# --- Verification Functions

def verify_openai_api_key(api_key):
    """
    Verifies that the OpenAI API key is correctly formatted and actually valid by making a real API call.
    Raises ValueError if the key is invalid.
    """
    # Local check
    if api_key is None or api_key == "":
        raise ValueError("The provided OpenAI API key is empty. Please check your key.")

    # Live API check
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=5)
    except requests.RequestException as e:
        raise ValueError(f"Network error when verifying OpenAI API key: {e}")

    if response.status_code != 200:
        raise ValueError(f"OpenAI API key validation failed: {response.status_code} - {response.text}")

    return api_key

def verify_anthropic_api_key(api_key):
    """
    Verifies that the Anthropic API key is correctly formatted and actually valid by making a real API call.
    Raises ValueError if the key is invalid.
    """
    # Local check
    if api_key is None or api_key == "":
        raise ValueError("The provided Anthropic API key is empty. Please check your key.")

    # Live API check
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    try:
        response = requests.get("https://api.anthropic.com/v1/models", headers=headers, timeout=5)
    except requests.RequestException as e:
        raise ValueError(f"Network error when verifying Anthropic API key: {e}")

    if response.status_code != 200:
        raise ValueError(f"Anthropic API key validation failed: {response.status_code} - {response.text}")

    return api_key

def verify_azure_api_key(api_key, model_provider):
    """
    Verifies the Azure API key depending on whether the model provider is 'openai' or 'anthropic'.
    Reuses the existing verify_openai_api_key or verify_anthropic_api_key functions.

    Args:
        api_key (str): The Azure API key to verify.
        model_provider (str): The provider, either 'openai' or 'anthropic'.

    Raises:
        ValueError: If the provider is unknown or key is invalid.

    Returns:
        str: The valid API key.
    """
    if model_provider.lower() == "openai":
        return verify_openai_api_key(api_key)
    elif model_provider.lower() == "anthropic":
        return verify_anthropic_api_key(api_key)
    else:
        raise ValueError(f"Unknown model provider '{model_provider}'. Must be 'openai' or 'anthropic'.")

# --- API Key Loader
def load_api_key(model_provider: str) -> dict:
    """
    Load and verify the correct API key(s) based on the model provider.

    Args:
        model_provider (str): The provider name, e.g., "openai", "anthropic", "azure-openai"

    Returns:
        dict: A dictionary containing the relevant API key(s).
    """
    load_dotenv()  # Load environment variables from .env file

    if model_provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        verify_openai_api_key(api_key)
        return {"openai_api_key": api_key}

    elif model_provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        verify_anthropic_api_key(api_key)
        return {"anthropic_api_key": api_key}

    elif model_provider == "azure-openai":
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_api_key is None or azure_api_key == "":
            raise ValueError("Azure OpenAI API key is missing.")
        if azure_endpoint is None or azure_endpoint == "":
            raise ValueError("Azure OpenAI endpoint is missing.")
        verify_openai_api_key(azure_api_key)
        return {
            "azure_openai_api_key": azure_api_key,
            "azure_openai_endpoint": azure_endpoint
        }

    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {model_provider}. Either the API KEY is missing or the provider is not supported (e.g., ollama uses local models, hence no API KEY).")

if __name__ == "__main__":
    # Test block to check the loading, verifying, and initialization of the LLM stream.
    import sys

    print("=== LLM Initialization Test ===")

    # Allow user to choose model provider
    supported_providers = ["openai", "anthropic", "azure-openai"]

    print(f"Supported providers: {supported_providers}")
    model_provider = input("Enter the model provider: ").strip().lower()

    if model_provider not in supported_providers:
        print(f"Error: Unsupported provider '{model_provider}'. Supported providers are {supported_providers}")
        sys.exit(1)

    # model_name = input(f"Enter the model name: e.g., {models_available[model_provider]}: ").strip().lower()
    # if model_name not in models_available[model_provider]:
    #     print(f"Error: Unsupported model '{model_name}' for provider '{model_provider}'.")
    #     print(f"Supported models for '{model_provider}': {models_available[model_provider]}")
    #     sys.exit(1)

    try:
        # Load and verify API keys
        print(f"\n[1/3] Loading API keys for provider '{model_provider}'...")
        api_keys = load_api_key(model_provider)
        print("[OK] API keys loaded and verified.")

        # Initialize LLM stream
        # print(f"[2/3] Initializing LLM stream for model '{model_name}'...")
        # llm = llm_stream_init(model_provider, model_name, api_key=api_keys)
        # print("[OK] LLM stream initialized successfully.")

        # Final confirmation
        print("\n=== All steps completed successfully! ===")

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        sys.exit(1)
