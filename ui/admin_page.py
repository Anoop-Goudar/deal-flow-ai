from __future__ import annotations

import json

import streamlit as st

from models import ConversationEvent
from dependencies import pipeline_service
from state import store


def render_admin_page() -> None:
    st.header("Admin Page")

    client_ids = sorted(store.clients.keys())
    selected_client_id = st.selectbox("Client", client_ids, key="admin_client")

    conversation_payload = [
        event.model_dump(mode="json") for event in store.conversations.get(selected_client_id, [])
    ]
    edited_json = st.text_area(
        "Mock conversation JSON",
        value=json.dumps(conversation_payload, indent=2),
        height=240,
    )

    action_col, reset_col = st.columns(2)
    with action_col:
        if st.button("Apply JSON", key="admin_apply_json"):
            try:
                parsed = json.loads(edited_json)
                conversation = [ConversationEvent.model_validate(item) for item in parsed]
                store.replace_conversation(selected_client_id, conversation)
                st.success("Conversation updated from JSON.")
                st.rerun()
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"Could not update conversation: {exc}")

        if st.button("Run Pipeline", key="admin_run_pipeline"):
            pipeline_service.run(selected_client_id)
            st.success("Pipeline executed.")

    with reset_col:
        if st.button("Reset Demo State", key="admin_reset_state"):
            store.reset()
            st.success("Demo state reset.")
            st.rerun()

    try:
        parsed = json.loads(edited_json)
        st.caption(f"Loaded {len(parsed)} conversation event(s) in editor preview.")
    except json.JSONDecodeError:
        st.error("Conversation JSON is not valid.")

    latest_result = store.recommendations.get(selected_client_id)
    if latest_result is not None:
        st.subheader("Latest Pipeline Output")
        st.json(latest_result.model_dump(mode="json"))

    st.subheader("Current Tasks")
    if not store.tasks:
        st.write("No tasks available.")
    for task in store.tasks:
        st.write(f"{task.task_id}: {task.client_id} -> {task.action} [{task.status}]")
