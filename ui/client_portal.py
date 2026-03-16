from __future__ import annotations

import streamlit as st

from dependencies import conversation_service, pipeline_service
from models import AddMessageRequest
from state import store


def render_client_portal() -> None:
    st.header("Client Portal")
    client_ids = sorted(store.clients.keys())
    selected_client_id = st.selectbox("Client", client_ids, key="client_portal_client")
    client = store.clients[selected_client_id]

    st.subheader(client.name)
    st.caption(f"Client ID: {client.client_id}")

    conversation = conversation_service.get_conversation(selected_client_id)
    st.markdown("### Conversation Timeline")
    for event in conversation:
        speaker = event.actor.replace("_", " ").title()
        with st.chat_message("user" if event.actor == "client" else "assistant"):
            st.markdown(f"**{speaker}**")
            st.write(event.message)

    latest_result = store.recommendations.get(selected_client_id)
    if latest_result is not None:
        st.markdown("### Latest AI Summary")
        st.info(latest_result.summary)

    with st.form("client_message_form", clear_on_submit=True):
        message = st.text_area("Send a message", placeholder="Share your business needs or missing details")
        submitted = st.form_submit_button("Send")
        if submitted and message.strip():
            conversation_service.add_message(
                AddMessageRequest(client_id=selected_client_id, actor="client", message=message.strip())
            )
            pipeline_service.run(selected_client_id)
            st.success("Message sent and analysis updated.")
            st.rerun()
