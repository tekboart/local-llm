import streamlit as st
import uuid
import os

from config import IMG_DIR

from utils.tekboart.nlp.utils.formatting import LLM_INSTRUCTION
st.warning(LLM_INSTRUCTION)

from streamlit_methods import (
    init_chat_opening,
)

def set_session_states():
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())

    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "system"  # default to system theme

    # TODO: Get the user_name based on the login credentials
    # E.g., Add Guest user too.
    if "user_name" not in st.session_state:
        st.session_state.user_name = "TekBoArt"

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
        # st.session_state.user_icon = os.path.join(IMG_DIR, f"{st.session_state.user_name.lower()}_pixel_art.png")
        st.session_state.user_icon = os.path.join(IMG_DIR, "avatar_user.png")

    # TODO: Get the llm_name based on the login credentials
    # E.g., if the user is Chirag, then use George as the LLM name
    if "llm_name" not in st.session_state:
        st.session_state.llm_name = "Robo TekBoArt"

    if "llm_icon" not in st.session_state:
        # llm_icon = "🤖"
        # llm_icon = ":material/robot_2:"
        # llm_icon = None  # None: uses the default icon (only if use st.write or st.markdown (not custom HTML))
        # st.session_state.llm_icon = os.path.join(IMG_DIR, f"{st.session_state['llm_name'].lower()}_pixel_art.png")
        st.session_state.llm_icon = os.path.join(IMG_DIR, "avatar_llm.png")

    if "instructions" not in st.session_state:
        st.session_state.instructions = [
            {
                "role": "user",
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