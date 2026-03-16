from __future__ import annotations

import html

import streamlit as st

from dependencies import conversation_service, pipeline_service
from models import AddMessageRequest
from state import store


def render_agent_dashboard() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(231, 94, 55, 0.18), transparent 28%),
                radial-gradient(circle at bottom right, rgba(15, 76, 129, 0.18), transparent 30%),
                linear-gradient(180deg, #f7f2eb 0%, #f2eee7 100%);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }

        .agent-shell {
            font-family: "IBM Plex Sans", sans-serif;
        }

        .hero-panel {
            background: linear-gradient(135deg, #16324f 0%, #284c73 65%, #315d87 100%);
            color: #f8f3eb;
            border-radius: 24px;
            padding: 1.4rem 1.5rem 1.2rem 1.5rem;
            box-shadow: 0 24px 60px rgba(18, 33, 52, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 1rem;
        }

        .hero-kicker, .section-label {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: 0.08em;
            font-size: 0.76rem;
            text-transform: uppercase;
            opacity: 0.78;
        }

        .hero-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2rem;
            font-weight: 700;
            margin-top: 0.2rem;
            line-height: 1.05;
        }

        .hero-subtitle {
            margin-top: 0.5rem;
            max-width: 50rem;
            line-height: 1.5;
            font-size: 0.98rem;
            opacity: 0.92;
        }

        .glass-card {
            background: rgba(255, 252, 247, 0.85);
            border: 1px solid rgba(29, 56, 84, 0.12);
            border-radius: 22px;
            padding: 1.1rem 1.05rem;
            box-shadow: 0 14px 38px rgba(36, 47, 61, 0.08);
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
        }

        .mini-stat-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .mini-stat {
            background: rgba(255, 255, 255, 0.58);
            border: 1px solid rgba(22, 50, 79, 0.09);
            border-radius: 18px;
            padding: 0.85rem 0.9rem;
        }

        .mini-stat-label {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #5c6d7f;
            font-family: "Space Grotesk", sans-serif;
        }

        .mini-stat-value {
            margin-top: 0.35rem;
            font-size: 1.2rem;
            font-weight: 700;
            color: #17314a;
            font-family: "Space Grotesk", sans-serif;
        }

        .client-chip {
            display: block;
            border-radius: 18px;
            padding: 0.9rem 0.95rem;
            margin-bottom: 0.6rem;
            background: rgba(255, 255, 255, 0.66);
            border: 1px solid rgba(23, 49, 74, 0.08);
        }

        .client-chip.active {
            background: linear-gradient(135deg, #fdf2de 0%, #f4d9ae 100%);
            border-color: rgba(190, 118, 42, 0.35);
        }

        .client-name {
            font-family: "Space Grotesk", sans-serif;
            font-weight: 700;
            color: #1a324c;
        }

        .client-meta {
            color: #526171;
            font-size: 0.9rem;
            margin-top: 0.15rem;
        }

        .section-heading {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
            color: #17314a;
            margin-bottom: 0.8rem;
        }

        .summary-card {
            background: linear-gradient(180deg, #fff8ee 0%, #fffdf8 100%);
            border: 1px solid rgba(196, 152, 67, 0.18);
            border-radius: 20px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.9rem;
        }

        .need-pill {
            display: inline-block;
            margin: 0.2rem 0.35rem 0 0;
            padding: 0.42rem 0.72rem;
            border-radius: 999px;
            background: #f3e0bf;
            color: #764c12;
            font-size: 0.86rem;
            font-weight: 600;
        }

        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.8rem;
        }

        .detail-tile {
            background: rgba(248, 249, 251, 0.95);
            border-radius: 16px;
            padding: 0.78rem 0.85rem;
            border: 1px solid rgba(23, 49, 74, 0.07);
        }

        .detail-label {
            font-size: 0.78rem;
            color: #667687;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-family: "Space Grotesk", sans-serif;
        }

        .detail-value {
            margin-top: 0.28rem;
            color: #17314a;
            font-weight: 600;
        }

        .recommendation-card {
            border-radius: 22px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.9rem;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(23, 49, 74, 0.08);
            box-shadow: 0 14px 28px rgba(18, 33, 52, 0.07);
        }

        .recommendation-topline {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: center;
            margin-bottom: 0.75rem;
        }

        .recommendation-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: #17314a;
        }

        .confidence-badge, .status-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 0.28rem 0.65rem;
            font-size: 0.78rem;
            font-weight: 700;
        }

        .confidence-badge {
            background: #e1eef8;
            color: #28577d;
        }

        .status-eligible {
            background: #dcefdc;
            color: #29613a;
        }

        .status-incomplete {
            background: #f8eccd;
            color: #7a5b14;
        }

        .status-not-eligible {
            background: #f5d8d5;
            color: #7f3029;
        }

        .task-card {
            border-radius: 18px;
            padding: 0.9rem 0.95rem;
            margin-bottom: 0.75rem;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(23, 49, 74, 0.09);
        }

        .task-title {
            font-weight: 700;
            color: #17314a;
        }

        .task-meta {
            font-size: 0.9rem;
            color: #5e6d7e;
            margin-top: 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    client_ids = sorted(store.clients.keys())
    selected_client_id = st.selectbox("Client", client_ids, key="agent_dashboard_client")
    client = store.clients[selected_client_id]

    if selected_client_id not in store.recommendations:
        pipeline_service.run(selected_client_id)

    pipeline_result = store.recommendations.get(selected_client_id)
    visible_tasks = [task for task in store.tasks if task.client_id == selected_client_id]
    confidence = pipeline_result.confidence.title() if pipeline_result else "Pending"
    needs_count = len(pipeline_result.detected_needs) if pipeline_result else 0
    open_tasks = len([task for task in visible_tasks if task.status != "completed"])

    st.markdown('<div class="agent-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-kicker">DealFlow AI Workspace</div>
            <div class="hero-title">{html.escape(client.name)}</div>
            <div class="hero-subtitle">
                Relationship intelligence panel for high-context banking conversations, grounded recommendations,
                and coordinated specialist follow-through.
            </div>
            <div class="mini-stat-grid">
                <div class="mini-stat">
                    <div class="mini-stat-label">Confidence</div>
                    <div class="mini-stat-value">{html.escape(confidence)}</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-label">Detected Needs</div>
                    <div class="mini-stat-value">{needs_count}</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-label">Open Tasks</div>
                    <div class="mini-stat-value">{open_tasks}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1.05, 1.75, 1.35], gap="large")

    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Portfolio</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Client Radar</div>', unsafe_allow_html=True)
        for listed_client in conversation_service.list_clients():
            active_class = " active" if listed_client.client_id == selected_client_id else ""
            turnover = (
                f"${int(listed_client.business_turnover):,} turnover"
                if listed_client.business_turnover is not None
                else "Turnover pending"
            )
            st.markdown(
                f"""
                <div class="client-chip{active_class}">
                    <div class="client-name">{html.escape(listed_client.name)}</div>
                    <div class="client-meta">{html.escape(listed_client.client_id)} · {html.escape(turnover)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Profile</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Client Snapshot</div>', unsafe_allow_html=True)
        snapshot_items = {
            "Business Type": client.type.title(),
            "Years Active": client.business_years if client.business_years is not None else "Unknown",
            "Turnover": f"${int(client.business_turnover):,}" if client.business_turnover else "Unknown",
            "Collateral": _format_bool(client.collateral_available),
            "Trade Activity": _format_bool(client.import_export_activity),
        }
        st.markdown('<div class="detail-grid">', unsafe_allow_html=True)
        for label, value in snapshot_items.items():
            st.markdown(
                f"""
                <div class="detail-tile">
                    <div class="detail-label">{html.escape(label)}</div>
                    <div class="detail-value">{html.escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Dialogue</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Conversation Timeline</div>', unsafe_allow_html=True)
        for event in conversation_service.get_conversation(selected_client_id):
            role = "user" if event.actor == "client" else "assistant"
            with st.chat_message(role):
                st.markdown(f"**{event.actor.replace('_', ' ').title()}**")
                st.write(event.message)

        with st.form("agent_message_form", clear_on_submit=True):
            message = st.text_area(
                "Reply to client",
                placeholder="Ask for missing documents, confirm eligibility inputs, or coordinate next steps",
            )
            submitted = st.form_submit_button("Send Response", use_container_width=True)
            if submitted and message.strip():
                conversation_service.add_message(
                    AddMessageRequest(
                        client_id=selected_client_id,
                        actor="relationship_manager",
                        message=message.strip(),
                    )
                )
                pipeline_service.run(selected_client_id)
                st.success("Reply sent and analysis refreshed.")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        top_left, top_right = st.columns([1.4, 1])
        with top_left:
            st.markdown('<div class="section-label">AI Layer</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-heading">Insight Engine</div>', unsafe_allow_html=True)
        with top_right:
            if st.button("Refresh Analysis", key="run_agent_analysis", use_container_width=True):
                pipeline_service.run(selected_client_id)
                st.rerun()

        if pipeline_result is None:
            st.info("No recommendation yet. Refresh analysis to generate one.")
        else:
            need_pills = "".join(
                f'<span class="need-pill">{html.escape(need)}</span>' for need in pipeline_result.detected_needs
            )
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="section-label">Conversation Summary</div>
                    <div style="margin-top:0.35rem; color:#20384f; line-height:1.6;">
                        {html.escape(pipeline_result.summary)}
                    </div>
                    <div style="margin-top:0.8rem;">{need_pills}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            attributes = pipeline_result.extracted_attributes.model_dump()
            visible_attributes = {key: value for key, value in attributes.items() if value not in (None, [], "")}
            if visible_attributes:
                st.markdown('<div class="section-label">Extracted Client Data</div>', unsafe_allow_html=True)
                st.markdown('<div class="detail-grid">', unsafe_allow_html=True)
                for key, value in visible_attributes.items():
                    rendered_value = ", ".join(value) if isinstance(value, list) else str(value)
                    st.markdown(
                        f"""
                        <div class="detail-tile">
                            <div class="detail-label">{html.escape(key.replace('_', ' '))}</div>
                            <div class="detail-value">{html.escape(rendered_value)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-label" style="margin-top:1rem;">Recommendations</div>', unsafe_allow_html=True)
            for recommendation in pipeline_result.recommendations:
                st.markdown(
                    f"""
                    <div class="recommendation-card">
                        <div class="recommendation-topline">
                            <div class="recommendation-title">{html.escape(recommendation.product)}</div>
                            <div class="confidence-badge">Score {recommendation.confidence:.2f}</div>
                        </div>
                        <div style="margin-bottom:0.75rem;">
                            {_status_badge(recommendation.eligibility)}
                        </div>
                        <div class="detail-grid">
                            <div class="detail-tile">
                                <div class="detail-label">Assigned Agent</div>
                                <div class="detail-value">{html.escape(recommendation.assigned_agent.replace('_', ' ').title())}</div>
                            </div>
                            <div class="detail-tile">
                                <div class="detail-label">Next Action</div>
                                <div class="detail-value">{html.escape(recommendation.next_action)}</div>
                            </div>
                        </div>
                        <div style="margin-top:0.8rem;">
                            <div class="detail-label">Recommendation Why</div>
                            <div style="margin-top:0.25rem; line-height:1.55; color:#27415a;">
                                {html.escape(recommendation.rationale)}
                            </div>
                        </div>
                        <div style="margin-top:0.75rem;">
                            <div class="detail-label">Policy Evidence</div>
                            <div style="margin-top:0.25rem; line-height:1.55; color:#27415a;">
                                {html.escape(recommendation.policy_excerpt)}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if recommendation.missing_fields:
                    st.warning(f"Missing information: {', '.join(recommendation.missing_fields)}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Execution</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Task Board</div>', unsafe_allow_html=True)
        if not visible_tasks:
            st.write("No tasks created yet.")
        for task in visible_tasks:
            st.markdown(
                f"""
                <div class="task-card">
                    <div class="task-title">{html.escape(task.product)}</div>
                    <div class="task-meta">{html.escape(task.action)}</div>
                    <div style="margin-top:0.45rem;">{_status_badge(task.status.replace('_', ' ').title(), task=True)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            cols = st.columns([1, 1])
            if cols[0].button("Start", key=f"start_{task.task_id}", use_container_width=True) and task.status == "pending":
                store.update_task_status(task.task_id, "in_progress")
                st.rerun()
            if cols[1].button("Complete", key=f"complete_{task.task_id}", use_container_width=True) and task.status != "completed":
                store.update_task_status(task.task_id, "completed")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _format_bool(value: bool | None) -> str:
    if value is True:
        return "Available"
    if value is False:
        return "Not available"
    return "Unknown"


def _status_badge(value: str, task: bool = False) -> str:
    normalized = value.lower()
    if "eligible" in normalized and "not" not in normalized:
        css_class = "status-badge status-eligible"
    elif "not eligible" in normalized:
        css_class = "status-badge status-not-eligible"
    elif "incomplete" in normalized:
        css_class = "status-badge status-incomplete"
    elif "completed" in normalized:
        css_class = "status-badge status-eligible"
    elif "in progress" in normalized:
        css_class = "status-badge confidence-badge"
    elif task:
        css_class = "status-badge status-incomplete"
    else:
        css_class = "status-badge confidence-badge"
    return f'<span class="{css_class}">{html.escape(value)}</span>'
