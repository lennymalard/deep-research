import streamlit as st
from graph import graph

st.title("🕵️ Deep Research Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("What do you want to research?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status_container = st.status("Researching...", expanded=True)
        try:
            initial_state = {"user_query": user_input}
            final_report = ""
            for event in graph.stream(initial_state):
                for key, value in event.items():
                    if key == "generate_queries":
                        status_container.write("🤔 Generating search queries...")
                    elif key == "search":
                        status_container.write("🌐 Searching and scraping web pages...")
                    elif key == "review":
                        status_container.write("🧐 Reviewing findings...")
                    elif key == "write":
                        status_container.update(label="Writing Report", state="complete", expanded=False)
                        final_report = value["report"]

            st.markdown(final_report)
            st.session_state.messages.append({"role": "assistant", "content": final_report})

        except Exception as e:
            st.error(f"An error occurred: {e}")