import streamlit as st
import os
import re

from mongodb import save_lead
from rag import ask_rag
from build_index import build_knowledge_base

# ==================================
# Page Config
# ==================================

st.set_page_config(
    page_title="Zenfuture AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ==================================
# Create Folders
# ==================================

os.makedirs(
    "data/uploads",
    exist_ok=True
)

os.makedirs(
    "database",
    exist_ok=True
)

# ==================================
# Session State
# ==================================

if "lead_saved" not in st.session_state:
    st.session_state.lead_saved = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files_processed" not in st.session_state:
    st.session_state.uploaded_files_processed = []

# ==================================
# Sidebar
# ==================================

with st.sidebar:

    st.title("📚 Knowledge Base")

    uploaded_files = st.file_uploader(
        "Upload PDF Documents",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:

        new_files = False

        for uploaded_file in uploaded_files:

            if (
                uploaded_file.name
                not in st.session_state.uploaded_files_processed
            ):

                save_path = os.path.join(
                    "data/uploads",
                    uploaded_file.name
                )

                with open(
                    save_path,
                    "wb"
                ) as f:

                    f.write(
                        uploaded_file.getbuffer()
                    )

                st.session_state.uploaded_files_processed.append(
                    uploaded_file.name
                )

                new_files = True

        if new_files:

            with st.spinner(
                "Creating Knowledge Base..."
            ):

                try:

                    build_knowledge_base()

                    st.success(
                        "Knowledge Base Updated Successfully"
                    )

                except Exception as e:

                    st.error(
                        str(e)
                    )

    st.markdown("---")

    if st.button(
        "🔄 Rebuild Knowledge Base"
    ):

        with st.spinner(
            "Rebuilding Knowledge Base..."
        ):

            try:

                build_knowledge_base()

                st.success(
                    "Knowledge Base Rebuilt"
                )

            except Exception as e:

                st.error(
                    str(e)
                )

    st.markdown("---")

    if st.button(
        "🗑 Clear Chat"
    ):

        st.session_state.messages = []

        st.rerun()

# ==================================
# Main Page
# ==================================

st.title(
    "🤖 Zenfuture Technologies AI Assistant"
)

st.markdown(
    """
Ask questions about:

✅ Company Information

✅ Uploaded PDF Documents

"""
)

# ==================================
# Lead Collection
# ==================================

if not st.session_state.lead_saved:

    st.subheader(
        "Enter Your Details"
    )

    with st.form(
        "lead_form"
    ):

        name = st.text_input(
            "Name"
        )

        email = st.text_input(
            "Email"
        )

        phone = st.text_input(
            "Phone Number"
        )

        submit = st.form_submit_button(
            "Start Chat"
        )

        if submit:

            if (
                not name
                or not email
                or not phone
            ):

                st.error(
                    "Please fill all fields"
                )

            elif not re.match(
                r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
                email
            ):

                st.error(
                    "Invalid Email Address"
                )

            elif (
                not phone.isdigit()
                or len(phone) < 10
            ):

                st.error(
                    "Invalid Phone Number"
                )

            else:

                try:

                    save_lead(
                        name,
                        email,
                        phone
                    )

                    st.session_state.lead_saved = True

                    st.success(
                        "Details Saved Successfully"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        str(e)
                    )

# ==================================
# Chat Section
# ==================================

else:

    st.success(
        "AI Assistant Ready"
    )

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    prompt = st.chat_input(
        "Ask your question..."
    )

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message(
            "user"
        ):

            st.markdown(
                prompt
            )

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Please wait......"
            ):

                try:

                    response = ask_rag(
                        prompt
                    )

                except Exception as e:

                    response = (
                        f"Error: {e}"
                    )

                st.markdown(
                    response
                )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response
            }
        )