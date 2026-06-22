import logging
logger = logging.getLogger(__name__)

import os
import dotenv
import streamlit as st
from typing import Iterator, List

from datetime import datetime

# pip install docx2txt, pypdf
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain.schema import HumanMessage, AIMessage, SystemMessage, ChatMessage, BaseMessage

from html_templates import (
    assistant_template,
    user_template,
)

from utils.tekboart.general.functional_programming import flatten
from utils.tekboart.nlp.rag.vectordb import retrieve_relevant_docs, format_retrieved_docs

# Load .env variables into environment
dotenv.load_dotenv()

os.environ["USER_AGENT"] = "myagent"

import base64

# NOTE: Without this function, the images will not be displayed in the HTML template
# As, Streamlit runs a web server, and your local file paths aren't automatically exposed to the browser.
def get_base64_image(image_path):
    """
    Convert an image to base64 string for embedding in HTML.
        * Only supports JPEG and PNG formats (for now).
    """
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/jpeg" if ext == ".jpg" else "image/png" if ext == ".png" else None

    if not mime_type:
        raise ValueError("Unsupported image format. Only .jpg and .png are allowed.")

    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
        return f"data:{mime_type};base64,{encoded}"

def _create_chatbox_nohtml(role:str, message: str, output_obj=st):
    with output_obj.chat_message(
        name=role,
        avatar=st.session_state.user_icon if role == "user" else st.session_state.llm_icon,  # Ensure llm_icon is a valid image path
    ):
        output_obj.write(message)

def _create_chatbox_html(role: str, message: str, output_obj=st):
    if role == "user":
        output_obj.write(user_template.format(avatar_icon=f"{get_base64_image(st.session_state.user_icon)}", message=message), unsafe_allow_html=True)
    elif role == "assistant":
        output_obj.write(assistant_template.format(avatar_icon=f"{get_base64_image(st.session_state.llm_icon)}", message=message), unsafe_allow_html=True)
    else:
        raise ValueError(f"Unknown role: {role}")

def output_chat_msg(role:str, message:str, output_obj=st, allow_html:bool=True):
    """
    Output the chat message based on the role (user or assistant).
    Args:
        role (str): The role of the message sender (user or assistant).
        message (str): The message content.
        output_obj: The Streamlit object to write the message to.
             * Default is st. But, you can use any other Streamlit object (like a placeholder).
    """
    if allow_html:
        _create_chatbox_html(role, message, output_obj)
    else:
        _create_chatbox_nohtml(role, message, output_obj)
    # if role == "user":
    #     if allow_html:
    #         output_obj.write(user_template.format(avatar_icon=f"{get_base64_image(st.session_state.user_icon)}", message=message), unsafe_allow_html=allow_html)
    #     else:
    #         output_obj.write()
    # elif role == "assistant":
    #     output_obj.write(assistant_template.format(avatar_icon=f"{get_base64_image(st.session_state.llm_icon)}", message=message), unsafe_allow_html=allow_html)
    # else:
    #     raise ValueError(f"Unknown role: {role}")


def output_chat_history(messages: list[dict], allow_html:bool=True):
    for message in messages:
        output_chat_msg(message['role'], message['content'], allow_html=allow_html)


from streamlit.elements.widgets.chat import ChatInputValue
def user_query_processor(user_query: ChatInputValue, chat_key: str = "chat_history", context_key: str = "chat_input_contexts"):
    """
    Process the user query and return the processed query.

    Args:
        user_query (ChatInputValue/dict): The user query dictionary.
        * The user_query acts as a dictionary with the following keys: text, files
        chat_key (str): The key for the chat history in the session state.
        context_key (str): The key for the contexts (of the user chat input) in the session state.
            # NOTE: The files uploaded in the chat are not RAG, but only added to the context window (in their entirety!)

    Returns:
        user_text (str): The processed user query text.
    """
    user_query_text = user_query['text']
    # NOTE: The files uploaded in the chat are not RAG, but only added to the context window (in their entirety!)
    user_query_files = user_query['files']
    # append the user query to the messages list

    is_chat_input_files = True if user_query_files else False
    if not is_chat_input_files:
        logger.info("No files uploaded, so the LLM is not using RAG.")
        user_text = user_query_text
        st.session_state.get(chat_key).append({"role": "user", "content": f"{user_text}"})
    else:
        logger.info("You have added non-RAG files to your chat input, (but a full files for context).")
        # TODO: Make this else statment a function
        documents = []

        # TODO: Make this loop a function (for loading files in memory)
        for file_chat_upload in user_query_files:
            from config import TEMP_UPLOAD_DIR
            temp_file_path = os.path.join(TEMP_UPLOAD_DIR, file_chat_upload.name)
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(file_chat_upload.getbuffer())
            # st.success(f"Saved: {file_chat_upload.name}")
            logger.info(f"created a temp file, for user chat input uploaded files: {temp_file_path}")

            from utils.tekboart.nlp.rag.loader import file_loader

            # make sure the temp file exists (beforing feeding it to my custom file_loader)
            assert os.path.exists(temp_file_path), f"File {temp_file_path} does not exist"
            # TODO: Add the option to load urls as well (using my custom url_loader)
            try: 
                docs = file_loader(temp_file_path)
            except KeyError as e:
                file_ext = temp_file_path.split(".")[-1]
                st.error(f"The file type \".{file_ext}\" is not supported")
                st.stop()

            documents.extend([{'file_name': file_chat_upload.name, 'loader': docs}])

            os.remove(temp_file_path)  # Remove the temp file after loading

        user_query_files_context = ',\n'.join(
            [
            "{{\n'file name': {filename},\n'file content': {content}\n}}".format(filename=file['file_name'], content='\n'.join([doc.page_content for doc in file['loader']]))
            # f"\n'file name': {file['file_name']},\n'content': {file['loader']}"
            for file in documents
            ]
        )
        # make it look like a JSON object (#TODO: use a for sophi approach)
        user_query_files_context = "[\n" + user_query_files_context + "\n]"

        # TODO: Maybe I can add a timestamp to the context (so the LLM can track and use the chronological order of contexts)
        st.session_state[context_key].append(
            {
                "role": "context",  # TODO: Can I use another role (e.g. "system" or "context")?
                "content": user_query_files_context
            }
        )

        # TODO: Don't the file context to st.session_state.chat_history, but to the context window (i.e., the prompt that is sent to the LLM)
        # As we want the use to only see the use query and the final LLM response (anything else should be in the background)
        query_files_bullet = "Attached/Uploaded files:\n"
        for file_chat_upload in user_query_files:
            query_files_bullet += f'- "{file_chat_upload.name}"\n'

        user_text = user_query_text + '\n\n' + query_files_bullet

        st.session_state[chat_key].append(
            # {"role": "user", "content": f"Context (in JSON format):\n{user_query_files_context}\n\nUser query:\n{user_query_text}"}
            {"role": "user", "content": user_text}
        )
        # TODO: For debug only
        # st.write(st.session_state.chat_history)

        # free up the memory--as we don't need the files any more (we have loaded them into our session state contexts)
        del user_query_files

    return user_text, is_chat_input_files

def separate_think_tag(llm_response):
    """
    Separate the think tag from the response.
        * Useful for the LLMs to think and then answer. e.g., DeepSeek-R1
    """
    import re
    match = re.match(r"(THINK:)(.*)", llm_response, re.DOTALL)
    if match:
        think_part = match.group(2).strip()
        return llm_response, f"<think>{think_part}</think>"
    else:
        return llm_response, None

# Function to stream the response of the LLM
# def stream_llm_response(llm_stream, messages, allow_html:bool=True):
#     """
#     Args:
#         llm_stream: The LLM object, with stream enabled.
#             * So the response is outputted in chunks, rather than all at once.
#         messages: List of messages to send to the LLM.
#             * each message is a dict with the keys: role and content
#     """
#     response_text = ""

#     for chunk in llm_stream.stream(messages):
#         response_text += chunk.content
#         yield chunk

    # Separate the <think> tag from the response
    # response_text, _ = separate_think_tag(response_text)

    # append the response (as a single text chunk) to the session state
    # st.session_state.chat_history.append({"role": "assistant", "content": response_text})
    # return response_text

def output_stream_llm_response(message_stream:Iterator[BaseMessage], allow_html:bool=False) -> Iterator[str]:
    response_text = ""
    if allow_html:
        # create a placeholder object to update the response in the chat (in real-time)
        # otherwise, we should use st.write() to regenerate the whole chat box for each generated token
        response_box = st.empty()
        for chunk in message_stream:
            # st.warning(f"{chunk = }")
            # st.warning(f"{chunk.content = }")
            if isinstance(chunk, BaseMessage):
                response_text += chunk.content
            else:
                response_text += chunk
            # placeholder_obj.write(content, unsafe_allow_html=True)
            output_chat_msg(role='assistant', message=response_text, output_obj=response_box, allow_html=allow_html)
            yield ""  # Must yield something for st.write_stream to work
    else:
        for chunk in message_stream:
            response_text += chunk.content
            yield chunk

    # Separate the <think> tag from the response
    response_text, _ = separate_think_tag(response_text)

    st.session_state.chat_history.append({"role": "assistant", "content": response_text})

# def stream_llm_response_html(llm_stream, messages):
#     """
#     Args:
#         llm_stream: The LLM object, with stream enabled.
#             * So the response is outputted in chunks, rather than all at once.
#         messages: List of messages to send to the LLM.
#             * each message is a dict with the keys: role and content
#     """
#     response_text = ""

#     for chunk in llm_stream.stream(messages):
#         response_text += chunk.content
#         yield chunk


#     # Separate the <think> tag from the response
#     response_text, _ = separate_think_tag(response_text)

#     # append the response (as a single text chunk) to the session state
#     st.session_state.chat_history.append({"role": "assistant", "content": response_text})
#     return response_text

def init_chat_opening():
    """
    Initialize the chat opening message.
    """
    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": f'O Captain! My Captain!\n\nHow can I assist you today "{st.session_state.user_name}"?'
        }
    )

# st.button("Clear Chat", on_click=lambda: st.session_state.chat_history.clear(), type="primary")
def new_chat_init(allow_html:bool=True):
    """
    Clears the chat history and reinitializes the chat opening message.
    """
    # TODO: before clearing the chat history, save the chat history to a file (to be loaded later in the sidebar, as user's chat history (it should be saved in the local storage and for the specific user who was the user))
    states_to_be_cleared = [
            "chat_history",
            "chat_input_contexts",
            "rag_sources",
    ]
    for state in states_to_be_cleared:
        if st.session_state.get(state) is not None:
            st.session_state[state].clear()
    # st.runtime.legacy_caching.clear_cache()

    states_to_be_false = [
            "use_rag",
            "use_academic_db",
            "use_industry_db",
    ]

    for state in states_to_be_false:
        if st.session_state.get(state) is not None:
            st.session_state[state] = False

    states_to_be_none = [
            "user_vecdb",
            "academic_vecdb",
            "industry_vecdb",
    ]
    for state in states_to_be_none:
        if st.session_state.get(state) is not None:
            st.session_state[state] = None

    # st.write("Chat history cleared. You can start a new chat with the same model.")

    # start the opening conversation by the LLM
    init_chat_opening()
    # output_chat_history(st.session_state.chat_history, allow_html=allow_html)


def _create_llm_input(messages_with_roles: list[dict]) -> list[BaseMessage]:
    """
    Create the input for the LLM based on the role of the creator of the message.
    """
    message_type = {
        'user': HumanMessage,
        'assistant': AIMessage,
        'context': HumanMessage,
        'system': SystemMessage,
    }

    if not isinstance(messages_with_roles, list) or not isinstance(messages_with_roles[0], dict):
        raise ValueError(
                        "The {x} should be a list of dictionaries, containing the keys: 'role' and 'content'\n"
                        "Structure:\n"
                        '''\
                        [
                            {
                            "role": <a_string>,
                            "content": <a_string>
                            },
                            {
                            "role": <a_string>,
                            "content": <a_string>
                            },
                        ]\n\
                        '''
                        "An example:\n"
                        "{'role': 'user', 'content': 'Hello, how are you?'}"
        )

    inputs = [
        (
            message_type[msg["role"]](content=msg["content"])
        )
        for msg in messages_with_roles
    ]

    return inputs


def create_stream_input_combo(is_chat_input_files: bool, use_rag: bool) -> list[BaseMessage]:
    """Create the (pertinent) input for the LLM"""

    current_datetime = datetime.now().strftime("\tDate: %Y-%m-%d,\n\tTime: %H:%M:%S")
    st.session_state.instructions += [
        {
            "role": "system",
            "content": f"Current date and time is:\n{current_datetime}"
        }
    ]
    instructions = _create_llm_input(st.session_state.instructions)
    messages = _create_llm_input(st.session_state.chat_history)
    query = messages[-1].content  # Get the last message from the messages list (which is the user query)

    # FIXME: It's working if we want to give the file context to the LLM even if the current query doesn't contain any files (As it proved to improve the responses)
    #     # I don't know why, but the answers will be better if I add the contexts to the stream_input (even if they current user query does not contain any files)
    #     # NOTE: The question and the response is still in the message history (for the query that had files) but LLM fails to see it and thinks it has not answered the question (even though it had successfully before!!!)
    #     # In a nutshell, add teh contexts (regardless whether the user query has files or not) (which makes this if statement redundant)
    # chat_input_contexts = create_llm_input(st.session_state.chat_input_contexts) if is_chat_input_files else []  # only give the context if the user query has files attached
    chat_input_contexts = _create_llm_input(st.session_state.chat_input_contexts) if st.session_state.get("chat_input_contexts") else []

    if st.session_state.get("user_vecdb") and st.session_state.get("use_rag"):
        rag_docs_w_score = retrieve_relevant_docs(query, st.session_state.user_vecdb, top_k=3, thresh=None)
        user_db_rag_retrieved = [{'role': 'context', 'content': format_retrieved_docs([doc_score_tuple], format='json')} for doc_score_tuple in rag_docs_w_score]
        user_db_contexts = _create_llm_input(user_db_rag_retrieved)
    else:
        user_db_contexts = []

    academic_db_contexts = _create_llm_input(st.session_state.academic_vecdb) if st.session_state.get("use_academic_vecdb") else []
    industry_db_contexts = _create_llm_input(st.session_state.industry_vecdb) if st.session_state.get("use_industry_vecdb") else []

    # FIXME: [URGENT] We need a more structured way to handle the contexts (e.g., with a prompt structure)
    # Use the get_conversational_rag_chain() example in this file.
    # This way the model will understand better we we refer to different contexts (e.g., user_db_contexts, academic_db_contexts, industry_db_contexts)
    # stream_input = instructions + messages + chat_input_contexts + user_db_contexts + academic_db_contexts + industry_db_contexts

    stream_input_dict = {
        "instructions": instructions,
        "messages": messages,
        "chat_input_contexts": chat_input_contexts,
        "user_db_contexts": user_db_contexts,
        "academic_db_contexts": academic_db_contexts,
        "industry_db_contexts": industry_db_contexts,
    }

    return stream_input_dict

# --- Indexing Phase ---

from streamlit_vectordb import (
    initialize_vector_db,
    _split_and_load_docs,
    load_doc_to_db,
    load_url_to_db,
    # remove_from_vector_db
)


# --- Retrieval Augmented Generation (RAG) Phase ---


def _get_context_retriever_chain(vector_db, llm):
    retriever = vector_db.as_retriever()
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="messages"),
            ("user", "{input}"),
            (
                "user",
                "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation, focusing on the most recent messages.",
            ),
        ]
    )
    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)

    return retriever_chain


def get_conversational_rag_chain(llm, vector_db):
    retriever_chain = _get_context_retriever_chain(vector_db, llm)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful assistant. You will have to answer to user's queries.
                You will have some context to help with your answers, but now always would be completely related or helpful.
                You can also use your knowledge to assist answering the user's queries.\n
                {context}""",
            ),
            MessagesPlaceholder(variable_name="messages"),
            ("user", "{input}"),
        ]
    )
    stuff_documents_chain = create_stuff_documents_chain(llm, prompt)

    return create_retrieval_chain(retriever_chain, stuff_documents_chain)

# ----------------------------------------------------------

# NOTE: This is my custom func to merge both RAG and non-RAG responses
def stream_response_generator(llm_stream, stream_input: dict[List[BaseMessage]], use_rag: bool = False, vector_db = None) -> Iterator[str]:
    if not use_rag:
        llm_input = list(flatten(stream_input.values(), max_depth=1))
        st.toast("Streaming response without RAG.")
        response_gen = llm_stream.stream(input=llm_input)
    else:
        if vector_db is None:
            # raise ValueError("Vector DB is required for RAG. Please provide a valid vector_db.")
            st.toast("⚠️ At least one document/URL is required for RAG. Please provide a file/URL to continue, or turn off RAG.")
            st.stop()

        # method 1 (works 100%): using my custom RAG retrieval chain (less accurate, but faster)
        llm_input = list(flatten(stream_input.values(), max_depth=1))
        st.toast("Streaming response with RAG.")
        response_gen = llm_stream.stream(input=llm_input)


        # TODO: Use the get_conversational_rag_chain() to create a RAG chain with the LLM and vector DB
        # method 2: Using RAG chain with stream input (more accurate, but slower)
        # We give the entire message history for RAG retrieval, rather than just the last message
        message_history = stream_input.get("messages")[:-1]
        user_input = stream_input.get("messages")[-1].content  # Get the last message from the messages list

        # response_gen = get_conversational_rag_chain(llm_stream, vector_db).stream({
        #     "messages": stream_input.get("messages")[:-1],  # messages_history - user's last query
        #     "input": stream_input.get("messages")[-1]  # user query, that is the last message in the messages history
        # })

    return response_gen

# NOTE: This is the separate function (based on Youtube) to stream the RAG response
def stream_llm_rag_response(llm_stream, messages):
    conversation_rag_chain = get_conversational_rag_chain(llm_stream)
    response_message = "*(RAG Response)*\n"
    for chunk in conversation_rag_chain.pick("answer").stream(
        {"messages": messages[:-1], "input": messages[-1].content}
    ):
        response_message += chunk
        yield chunk

    st.session_state.messages.append({"role": "assistant", "content": response_message})

    return response_message

def lock_session_state_entry(key, default, warning_msg=None):
    """
    Lock the session state to prevent any changes to it.
        * Good for debugging, testing, and WIP features.
    Args:
        key (str): The key of the session state entry to lock.
        warning_msg (str): The warning message to display when the session state is locked.
            * Default is None, which will display a generic message.

    Raises:
        ValueError: If the session state entry is not a boolean.

    Example:
        # This prevents the user from changing the value of the session state entry "is_locked" (e.g., in a toggle).
        st.toggle(
            label="is_locked?",
            key="is_locked",
            on_change=lock_session_state_bool("is_locked", True, "Work in progress..."),
        )
    """
    if key not in st.session_state:
        raise ValueError(
            f"Session state entry '{key}' does not exist. "
            "Please, use a valid session state entry."
        )

    value = st.session_state.get(key)
    # Check if the value has the same type as the default value
    if not isinstance(default, value.__class__):
        raise ValueError(
            f"The default value '{default}' is not the same type as the session state entry '{key}'."
            "Please, use a valid default value."
        )

    if value != default:
        if warning_msg:
            display_msg = warning_msg
        else:
            display_msg = f"Session state entry '{key}' is locked to the value '{value}'."

        st.toast(display_msg, icon="⚠️")

    # Ankify: If a session_state entry is set by a component (e.g., toggle), to update the value afterwards:
    # Correct: st.session_state.update({'key': value})
    # Wrong: st.session_state.key = value

    # Keep the original value of the session state entry (buy inverting the value)
    st.session_state.update({key: default})

# --- CSS and HTML ---
def update_css(css:str, state_key:str="css"):
    """
    Update the CSS styles in the Streamlit app.
    """
    st.session_state[state_key] = css
    st.write(f"<style>{css}</style>", unsafe_allow_html=True)

# TODO: Update the css style based inside the session state (e.g., for the theme, dark/light)
def change_css(css:str, state_key:str="css", change_type:str="add", change_value:str=""):
    """
    Change the CSS styles in the Streamlit app.

    Args:
        css (str): The CSS styles to be added or modified.
        state_key (str): The key to store the CSS in the session state.
        change_type (str): The type of change to be made ("add", "remove", "update").
    """
    import re
    # TODO: Use regex to add, remove, or update the CSS styles
    if change_type == "add":
        css_changed = ""
    elif change_type == "remove":
        css_changed = ""
    elif change_type == "update":
        # css_changed = re.sub(r"(?<=})", f"\n{change_value}", css)
        css_changed = ""
    else:
        raise ValueError(f"Invalid change_type: {change_type}. Use 'add', 'remove', or 'update'.")

    # TODO: use update_css() function here to update after you made the change
    update_css(css_changed, state_key=state_key)
