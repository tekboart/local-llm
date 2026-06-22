import os
import uuid
import streamlit as st

# Set User-Agent globally for the process
os.environ["USER_AGENT"] = "MyStreamlitApp/1.0 (Linux; +https://example.com)"

# -- Constants (the ones that don't depend on the the session state) --
from config import (
    ALLOW_CUSTOM_HTML,
    MODELS,
    PRIVACY_POLICY,
    IMG_DIR,
    DB_DOCS_LIMIT,
    ROOT_PATH,
    DATA_DIR,
)

import logging
logger = logging.getLogger(__name__)

# check if it's linux so it works on Streamlit Cloud
# if os.name == "posix":
#     __import__("pysqlite3")
#     import sys

#     if sys.modules.get("pysqlite3"):
#         sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

# from langchain.schema import HumanMessage, AIMessage, SystemMessage, ChatMessage, BaseMessage

from streamlit_methods import (
    output_chat_msg,
    output_chat_history,
    new_chat_init,
    user_query_processor,
    create_stream_input_combo,
    stream_response_generator,
    output_stream_llm_response,
    lock_session_state_entry,
    update_css,
    init_chat_opening
    # change_css,
)

from streamlit_vectordb import (
    load_doc_to_db,
    load_url_to_db,
    init_embedding_func
)

from utils.tekboart.nlp.llms.llm import llm_chat_init
from utils.tekboart.nlp.llms.api import load_api_key

from utils.tekboart.web.css import load_css

from utils.tekboart.nlp.utils.formatting.llm_instruction import LLM_INSTRUCTION

# --- Page Config
st.set_page_config(
    page_title="TekBoArt's Local LLM",
    page_icon="🤖",
    layout="wide", # "centered" or "wide"
    initial_sidebar_state="expanded",
)

# --- CSS Styles ---
# Load CSS from file

# Inject CSS (Should be after set_page_config)
if ALLOW_CUSTOM_HTML:
    css = load_css(f"{ROOT_PATH}/style.css")
    update_css(css, state_key="css")

# --- Initial Setup: Set/Load Streamlit Session States ---
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "system"  # default to system theme

# TODO: Get the user_name based on the login credentials
# E.g., Add Guest user too.
if "user_name" not in st.session_state:
    st.session_state.user_name = "John Doe"

if "user_role" not in st.session_state:
    st.session_state.user_role = "Computer Vision Researcher"

if "role_requirements" not in st.session_state:
    st.session_state.role_requirements = (
        "The language should be formal and scientific, but please don't talk like Shakespeare. Be formal but modern and concise."
    )

if "user_icon" not in st.session_state:
    # user_icon = "👤"
    # user_icon = ":material/face:"
    # user_icon = None  # None: uses the default icon (only if use st.write or st.markdown (not custom HTML))
    # st.session_state.user_icon = os.path.join(IMG_DIR, f"{st.session_state.user_name.lower()}_cartoon.png")
    st.session_state.user_icon = os.path.join(IMG_DIR, "avatar_user.png")

# TODO: Get the llm_name based on the login credentials
# E.g., if the user is Chirag, then use George as the LLM name
if "llm_name" not in st.session_state:
    st.session_state.llm_name = "Robot TekBoArt"

if "llm_icon" not in st.session_state:
    # llm_icon = "🤖"
    # llm_icon = ":material/robot_2:"
    # llm_icon = None  # None: uses the default icon (only if use st.write or st.markdown (not custom HTML))
    # st.session_state.llm_icon = os.path.join(IMG_DIR, f"{st.session_state['llm_name'].lower()}_cartoon.png")
    st.session_state.llm_icon = os.path.join(IMG_DIR, "avatar_llm.png")

if "instructions" not in st.session_state:
    st.session_state.instructions = [
        {
            "role": "system",
            "content": LLM_INSTRUCTION
        },
        # {
        #     "role": "system",
        #     # "content": "You are a helpful assistant. Please answer the user's questions to the best of your ability.",
        #     # "content": "Say 'Hello' before each line",
        #     # "content": 'You are an AI assistant that provides accurate answers based on the retrieved documents (in "Context" section). Use the given context to answer queries concisely and avoid making up information.'
        #     # "content": 'You are a sarcastic but intelligent assistant. Respond helpfully, but with dry humour and witty remarks. Do not break character.'
        #     "content": "Please answer the user's questions to the best of your ability. If you don't know the answer, say 'I don't know'. Be as concise as you can and avoid meta commentary",
        # },
        {
            "role": "system",
            "content": f"The user is a {st.session_state.user_role}. The requirements to interact with this user is: {st.session_state.role_requirements}"
        }
    ]

# You can filter the messages based on the role (e.g., "user", "assistant", "system" or "context")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    init_chat_opening()

# the contexts is used to store the context of the files uploaded in the chat (but not in RAG)
if "chat_input_contexts" not in st.session_state:
    st.session_state.chat_input_contexts = []

if "local_llm" not in st.session_state:
    st.session_state.local_llm = True

if "model_provider" not in st.session_state:
    st.session_state.model_provider = None

if "model_name" not in st.session_state:
    st.session_state.model_name = None

if "use_rag" not in st.session_state:
    st.session_state.use_rag = False

# FIXME: How this and "user_vecdb" are different?
if "rag_sources" not in st.session_state:
    st.session_state.rag_sources = []

# "user_vecdb" is used to store the vector DB for the user uploaded sources
if "user_vecdb" not in st.session_state:
    st.session_state.user_vecdb = None

if "use_academic_db" not in st.session_state:
    st.session_state.use_academic_db = False

if "academic_vecdb" not in st.session_state:
    st.session_state.academic_vecdb = None

if "use_industry_db" not in st.session_state:
    st.session_state.use_industry_db = False

if "industry_vecdb" not in st.session_state:
    st.session_state.industry_vecdb = None

# --- Streamlit App Content ---

# st.divider()

# -- Main Content --

# - Load the vector DBs (if any) -
# TODO: Load the empty vector DBs for User's RAG sources (for upload)

# -- Sidebar --
with st.sidebar:
    # -- Header --
    # sidebar_header_cols = st.columns([0.2, 0.2, 0.2, 0.2, 0.2])
    # sidebar_header_cols[0].image(image=f"{ROOT_PATH}/images/logo.jpg")
    # sidebar_header_cols[1].image(image=f"{ROOT_PATH}/images/logo.png")
    # sidebar_header_cols[2].image(image=f"{ROOT_PATH}/images/logo.png")
    # sidebar_header_cols[3].image(image=f"{ROOT_PATH}/images/logo.png")

    sidebar_header_cols = st.columns([0.2, 0.8])
    sidebar_header_cols[0].image(image=f"{ROOT_PATH}/images/logo.gif")
    sidebar_header_cols[1].header("TekBoArt's Local LLM")

    st.html("<div style='size: 30px'</div")

    col_menu = st.columns(2)
    with col_menu[0]:
        # FIXME: This button doesn't work as expected (greys out the chat instead of clearing it)
        st.button("New Chat", on_click=new_chat_init, type="tertiary", icon=":material/edit_square:", use_container_width=False)
        st.button("Search Chats", on_click=lambda: st.toast("🚧 [WIP] This function is under construction"), type="tertiary", icon=":material/search:", use_container_width=False)
        st.button("Log out", on_click=lambda: st.toast("🚧 [WIP] This function is under construction"), type="tertiary", icon=":material/key:", use_container_width=False)

    st.html("<div style='size: 30px'</div")

    exp_llm_setting = st.expander(
        label="LLM Settings",
        icon=":material/smart_toy:",
        expanded=True,  # default to expanded
    )
    exp_llm_setting_cols = exp_llm_setting.columns(2)
    with exp_llm_setting_cols[0]:
        st.toggle(
            label="Local LLM?",
            # value=st.session_state.get("local_llm", True),  # default True, so the user has to enable it
            # value=True,
            key="local_llm",
            on_change=lock_session_state_entry("local_llm", True, "TekBoArt does not allow you to use online LLMs (e.g., OpenAI) on ETHICS protected material."),
        )

    model_options = MODELS['local'].keys() if st.session_state.local_llm else MODELS['non_local'].keys()
    exp_llm_setting.selectbox(
        label="🤖 Select a Model",
        options=model_options,
        key="model_title",
        label_visibility="collapsed",  # hide the label
        help="Hot-swap the model to use for the chat. Don't need to restart the app, the new model will remember previous answers (generated by another model).",
    )

    # Set the model provider and model name based on the selected model
    #TODO: Call a function to download all the models in the MODELS_LOCAL (if they are not already downloaded)
    # Use my "llm_simple.py" script to download the models and output errors (if any)
    if st.session_state.local_llm:
        st.session_state.model_provider, *_, st.session_state.model_name = MODELS['local'][st.session_state.model_title].split("/")
    else:
        st.session_state.model_provider, *_, st.session_state.model_name = MODELS['non_local'][st.session_state.model_title].split("/")

    # -- init + Verify the LLM --
    if st.session_state.local_llm:
        llm_stream = llm_chat_init(st.session_state.model_provider, st.session_state.model_name)
        # init the embedding function based on the local setting
        from utils.tekboart.nlp.rag.vectordb import init_embedding_func_ollama
        from langchain_ollama import OllamaEmbeddings
        st.session_state.embed_func = init_embedding_func_ollama(OllamaEmbeddings, st.session_state.model_name)
    else:
        # just check if the API key is set and is valid, but don't save it to a variable (as it's might be sensitive)
        load_api_key(st.session_state.model_provider)
        llm_stream = llm_chat_init(st.session_state.model_provider, st.session_state.model_name, load_api_key(st.session_state.model_provider), auto_pull=True, streaming=True)
        # TODO: Add the embedding function for the non-local LLMs (e.g., OpenAI, Azure, etc.)

    exp_rag_setting = st.expander(
        label="RAG Settings",
        icon=":material/database_search:",
        expanded=False,
    )

    exp_rag_setting_cols = exp_rag_setting.columns(2)
    with exp_rag_setting_cols[0]:
        is_user_vecdb_loaded = (
            "user_vecdb" in st.session_state and st.session_state.get("user_vecdb") is not None
        )
        st.toggle(
            "💾 Use RAG",
            value=False,  # default False, so the user has to enable it
            key="use_rag",
            # disabled=not is_vector_db_loaded,
            # on_change=lock_session_state_entry("use_rag", is_user_vecdb_loaded, "The \"st.session_state.user_vecdb\" is not loaded. Please load the vector DB to continue."),
        )
        # TODO: ADD this to where we select the model
        # if st.session_state.use_rag and not is_user_vecdb_loaded:
        #     # from langchain_ollama import OllamaEmbeddings
        #     # embedding_function = init_embedding_func(st.session_state.local_llm, OllamaEmbeddings, )
        #     docs =
        #     from utils.tekboart.nlp.rag.vectordb import chromadb_init
        #     st.session_state.user_vecdb = chromadb_init(
        #         DATA_DIR,
        #         em
        #     )

    if st.session_state.use_rag:
        exp_rag_setting.header("Use academic knowledge base", divider=True)
        cols2 = exp_rag_setting.columns(2)
        with cols2[0]:
            is_academic_vecdb_loaded = (
                "academic_vecdb" in st.session_state and st.session_state.get("academic_vecdb") is not None
            )
            # We cannot easily style the st.toggle, so we use st.checkbox instead
            # st.toggle --> st.checkbox (All the args are the same)
            st.checkbox(
                "📚 Academic",
                value=False,  # default False, so the user has to enable it
                key="use_academic_db",
                # disabled=not is_vector_db_loaded,
                on_change=lock_session_state_entry("use_academic_db", is_academic_vecdb_loaded, "[WIP] The TekBoArt 'Academic' Knowledge Base is not available yet"),
                help="Use the TekBoArt 'Academic' Knowledge Base to be considered for your questions.",
            )
        with cols2[1]:
            is_industry_vecdb_loaded = (
                "industry_vecdb" in st.session_state and st.session_state.get("industry_vecdb") is not None
            )
            st.checkbox(
                "📚 Industry",
                value=False,  # default False, so the user has to enable it
                key="use_industry_db",
                # disabled=not is_vector_db_loaded,
                on_change=lock_session_state_entry("use_industry_db", False, "[WIP] The TekBoArt 'Industry' Knowledge Base is not available yet"),
                help="Use the TekBoArt 'Industry' Knowledge Base to be considered for your questions.",
            )

        # Show the RAG options only if the vector DB is loaded
        exp_rag_setting.header("Add your own sources:", divider=True)

        # File upload input for RAG with documents
        exp_rag_setting.file_uploader(
            label="📄 Upload a document",
            type=["pdf", "txt", "docx", "md", "xlsx", "pptx", "jpg", "jpeg",
                  "png", "webp"],  # add more file types if supported by file_loader (e.g., .url files)
            accept_multiple_files=True,
            # on_change=load_doc_to_db(db_docs_limit=DB_DOCS_LIMIT, embedding_function=embedding_function, db_name=st.session_state.user_vecdb),
            on_change=load_doc_to_db(db_docs_limit=DB_DOCS_LIMIT, embedding_function=st.session_state.embed_func, db_name="user_vecdb"),
            key="rag_docs",
        )

        # URL input for RAG with websites
        exp_rag_setting.text_input(
            label="🌐 Add a URL",
            placeholder="https://example.com",
            # on_change=load_url_to_db,
            on_change=load_url_to_db(embedding_function=st.session_state.embed_func, db_name="user_vecdb", sub_pages=False),
            key="rag_url",
            help="Needs internet connection, but the LLM is still local.",
        )

        # Display the VectorDB (if any)
        exp_rag_setting.toggle(
            "📚 Use your uploaded files?",
            value=is_user_vecdb_loaded,
            key="vector_db",
            disabled=not is_user_vecdb_loaded,
        )
        if st.session_state.vector_db:
            with exp_rag_setting.container(
                border=True,
            ):
                st.write(
                    "⚠️ The DB is empty ⚠️"
                    if not is_user_vecdb_loaded
                    else [source for source in st.session_state.rag_sources]
                )

    # # Information about the app
    # st.divider()
    # # TODO: add a funny GIF/Video here (related to the center)
    # # st.video("https://youtu.be/")
    # st.image(
    #     image=f"{ROOT_PATH}/images/logo.png",
    #     caption="TekBoArt Logo",
    #     use_container_width=True,
    # )

    # st.write("🌏️[TekBoArt Official Website](https://github.com/tekboart.com/)")
    # st.write("🌏[GitHub Repo](https://github.com/tekboart/local-llm)")

# -- chat part --
output_chat_history(st.session_state.chat_history, allow_html=ALLOW_CUSTOM_HTML)

# Get user input, (1) print it as user message, (2) get the response from LLM and print it as AI response
# TODO: Make this a function in 'streamlit_methods.py'
if user_query := st.chat_input(placeholder="Your message (Supports Markdown)", key='chat_input', accept_file='multiple'):
    # -- Process the user query --
    user_text, is_chat_input_files = user_query_processor(user_query, "chat_history", "chat_input_contexts")
    # display the user query
    output_chat_msg(role='user', message=user_text, allow_html=ALLOW_CUSTOM_HTML)

    # --- Generate AI response
    # -- Create the Input for the LLM --
    stream_input = create_stream_input_combo(
        is_chat_input_files=is_chat_input_files,
        use_rag=st.session_state.use_rag
    )

    # Get the response from the LLM (as a generator)
    # if st.session_state.use_rag and st.session_state.rag
    response_gen = stream_response_generator(
        llm_stream,
        stream_input,
        st.session_state.use_rag,
        st.session_state.user_vecdb,
    )

    # method 1: Needs to replace the html every time (works 100%)
    # stream_llm_response(response_gen, allow_html=ALLOW_CUSTOM_HTML)
    # method 2: doesn't need to replace the html every time (works 100%)
    # NOTE: I THINK WE SHOULD with st.chat_message (IF NOT USING ALLOW_CUSTOM_HTML) USE THE stream_llm_response() FUNCTION
    if ALLOW_CUSTOM_HTML:
        st.write_stream(output_stream_llm_response(response_gen, allow_html=ALLOW_CUSTOM_HTML))
    else:
        with st.chat_message(name="assistant", avatar=st.session_state.llm_icon):
            st.write_stream(output_stream_llm_response(response_gen))

# Instead of using "streamlit run app_web.py", use the following command to start the server
import subprocess
import webbrowser
import time


# FIXME: Doesn't work
def start_server(
    file: str = "app_web.py",
    url: str = "http://localhost",
    port: int = 8501,
    wait_time: int = 1,
):
    """
    Starts a server using the given command and opens a web browser with the specified URL and port.

    :param command: The command to start the server (default: 'streamlit run app_web.py').
    :param url: The base URL to open in the web browser (default: 'http://localhost').
    :param port: The port number where the server runs (default: 8501).
    :param wait_time: Time to wait before opening the browser (default: 1 seconds).
    """
    # Start the process
    process = subprocess.Popen(f"streamlit run {file}", shell=True)

    # Wait for the server to start
    time.sleep(wait_time)

    # Construct the full URL
    full_url = f"{url}:{port}"

    # Open the web browser
    webbrowser.open(full_url)

    return process  # Return the process in case you need to manage it


# Example usage
if __name__ == "__main__":
    logger.info("The %s is being run as the main module.", __file__)

    # Start the Streamlit server
    # FIXME: This doesn't work as streamlit restarts itself recursively in an infinite loop.
    # start_server()
