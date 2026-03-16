import { useEffect, useState } from "react";
import { api } from "./api";

const pages = ["Agent Dashboard", "Client Portal", "Admin Page"];

export default function App() {
  const [page, setPage] = useState("Agent Dashboard");
  const [clients, setClients] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState("");
  const [workspace, setWorkspace] = useState(null);
  const [messageDraft, setMessageDraft] = useState("");
  const [clientDraft, setClientDraft] = useState("");
  const [conversationJson, setConversationJson] = useState("[]");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    void refreshAll();
  }, []);

  useEffect(() => {
    if (!selectedClientId && clients.length > 0) {
      setSelectedClientId(clients[0].client_id);
    }
  }, [clients, selectedClientId]);

  useEffect(() => {
    if (selectedClientId) {
      void refreshClient(selectedClientId);
    }
  }, [selectedClientId]);

  async function refreshAll() {
    setLoading(true);
    setError("");
    try {
      const nextClients = await api.getClients();
      setClients(nextClients);
      if (!selectedClientId && nextClients.length > 0) {
        setSelectedClientId(nextClients[0].client_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function refreshClient(clientId) {
    try {
      const nextWorkspace = await api.getWorkspace(clientId);
      applyWorkspace(nextWorkspace);
    } catch (err) {
      setError(err.message);
    }
  }

  function applyWorkspace(nextWorkspace) {
    setWorkspace(nextWorkspace);
    setConversationJson(JSON.stringify(nextWorkspace.conversation, null, 2));
    setClients((currentClients) =>
      currentClients.map((client) =>
        client.client_id === nextWorkspace.client.client_id ? nextWorkspace.client : client,
      ),
    );
  }

  async function syncData(clientId = selectedClientId) {
    await refreshAll();
    if (clientId) {
      await refreshClient(clientId);
    }
  }

  async function handleSend(actor, draft, clear) {
    if (!selectedClientId || !draft.trim()) {
      return;
    }
    const trimmed = draft.trim();
    setBusy(true);
    setBusyLabel("Running pipeline...");
    setError("");
    clear("");
    const optimisticEvent = {
      timestamp: new Date().toISOString(),
      actor,
      message: trimmed,
      optimistic: true,
    };
    setWorkspace((currentWorkspace) => {
      if (!currentWorkspace) {
        return currentWorkspace;
      }
      const nextWorkspace = {
        ...currentWorkspace,
        conversation: [...currentWorkspace.conversation, optimisticEvent],
      };
      setConversationJson(JSON.stringify(nextWorkspace.conversation, null, 2));
      return nextWorkspace;
    });
    try {
      const response = await api.addMessage({
        client_id: selectedClientId,
        actor,
        message: trimmed,
      });
      applyWorkspace(response.workspace);
    } catch (err) {
      setError(err.message);
      await refreshClient(selectedClientId);
    } finally {
      setBusy(false);
      setBusyLabel("");
    }
  }

  async function handleRunAnalysis() {
    if (!selectedClientId) {
      return;
    }
    setBusy(true);
    setBusyLabel("Running pipeline...");
    setError("");
    try {
      const nextWorkspace = await api.runPipeline(selectedClientId);
      applyWorkspace(nextWorkspace);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      setBusyLabel("");
    }
  }

  async function handleTaskUpdate(taskId, status) {
    setBusy(true);
    setBusyLabel("Updating task...");
    setError("");
    try {
      await api.updateTask(taskId, status);
      await syncData(selectedClientId);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      setBusyLabel("");
    }
  }

  async function handleReset() {
    setBusy(true);
    setBusyLabel("Resetting demo...");
    setError("");
    try {
      await api.resetDemo();
      await syncData(selectedClientId);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      setBusyLabel("");
    }
  }

  const selectedClient = clients.find((client) => client.client_id === selectedClientId) || null;
  const pipelineResult = workspace?.pipeline_result || null;
  const clientTasks = workspace?.tasks || [];
  const conversation = workspace?.conversation || [];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-card">
          <p className="eyebrow">DealFlow AI</p>
          <h1>Relationship Banking</h1>
          <p className="brand-copy">
            A quieter workspace for AI-assisted deal flow and specialist coordination.
          </p>
        </div>

        <div className="sidebar-card">
          <p className="eyebrow">Portfolio</p>
          <div className="client-list">
            {clients.map((client) => (
              <button
                key={client.client_id}
                type="button"
                className={`client-button ${client.client_id === selectedClientId ? "active" : ""}`}
                onClick={() => setSelectedClientId(client.client_id)}
              >
                <span className="client-button-name">{client.name}</span>
                <span className="client-button-meta">
                  {client.client_id} ·{" "}
                  {client.business_turnover ? `$${Number(client.business_turnover).toLocaleString()}` : "Pending"}
                </span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      <main className="main-panel">
        {!loading && busyLabel ? (
          <div className="blocking-overlay" role="status" aria-live="polite" aria-busy="true">
            <div className="blocking-modal">
              <div className="spinner" />
              <strong>{busyLabel}</strong>
              <span>Please wait while DealFlow AI updates the workspace.</span>
            </div>
          </div>
        ) : null}

        <div className="topbar">
          <div className="page-nav inline">
            {pages.map((item) => (
              <button
                key={item}
                type="button"
                className={`page-tab ${page === item ? "active" : ""}`}
                onClick={() => setPage(item)}
              >
                {item}
              </button>
            ))}
          </div>
          {selectedClient ? (
            <div className="topbar-client">
              <span>{selectedClient.client_id}</span>
              <strong>{selectedClient.name}</strong>
            </div>
          ) : null}
        </div>

        <header className="hero">
          <div>
            <p className="eyebrow">Active Client</p>
            <h2>{selectedClient ? selectedClient.name : "Loading..."}</h2>
            <p className="hero-copy">
              A focused relationship view with conversation, recommendation, and execution in one place.
            </p>
          </div>
          <div className="hero-stats">
            <StatCard label="Confidence" value={pipelineResult?.confidence || "Pending"} />
            <StatCard label="Detected Needs" value={pipelineResult?.detected_needs?.length || 0} />
            <StatCard
              label="Open Tasks"
              value={clientTasks.filter((task) => task.status !== "completed").length}
            />
          </div>
        </header>

        {error ? <div className="error-banner">{error}</div> : null}
        {loading ? <div className="loading-panel">Loading workspace...</div> : null}

        {!loading && page === "Agent Dashboard" ? (
          <AgentDashboard
            selectedClient={selectedClient}
            conversation={conversation}
            pipelineResult={pipelineResult}
            tasks={clientTasks}
            replySuggestions={workspace?.suggested_replies || []}
            messageDraft={messageDraft}
            setMessageDraft={setMessageDraft}
            onSend={() => handleSend("relationship_manager", messageDraft, setMessageDraft)}
            onRunAnalysis={handleRunAnalysis}
            onTaskUpdate={handleTaskUpdate}
            busy={busy}
          />
        ) : null}

        {!loading && page === "Client Portal" ? (
          <ClientPortal
            selectedClient={selectedClient}
            conversation={conversation}
            pipelineResult={pipelineResult}
            clientDraft={clientDraft}
            setClientDraft={setClientDraft}
            onSend={() => handleSend("client", clientDraft, setClientDraft)}
            busy={busy}
          />
        ) : null}

        {!loading && page === "Admin Page" ? (
          <AdminPage
            conversationJson={conversationJson}
            setConversationJson={setConversationJson}
            pipelineResult={pipelineResult}
            onRunAnalysis={handleRunAnalysis}
            onReset={handleReset}
            busy={busy}
          />
        ) : null}
      </main>
    </div>
  );
}

function AgentDashboard({
  selectedClient,
  conversation,
  pipelineResult,
  tasks,
  replySuggestions,
  messageDraft,
  setMessageDraft,
  onSend,
  onRunAnalysis,
  onTaskUpdate,
  busy,
}) {
  const visibleAttributes = pipelineResult
    ? Object.entries(pipelineResult.extracted_attributes || {}).filter(([, value]) => {
        return value !== null && value !== "" && !(Array.isArray(value) && value.length === 0);
      })
    : [];

  return (
    <section className="workspace-grid">
      <div className="panel conversation-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Dialogue</p>
            <h3>Conversation Timeline</h3>
          </div>
        </div>
        <div className="chat-thread">
          {conversation.map((event) => (
            <article
              key={`${event.timestamp}-${event.actor}-${event.message}`}
              className={`message-card ${event.actor === "client" ? "client" : "agent"}`}
            >
              <div className="message-meta">{event.actor.replaceAll("_", " ")}</div>
              <p>{event.message}</p>
            </article>
          ))}
        </div>
        {replySuggestions.length > 0 ? (
          <div className="suggestion-strip">
            <div className="suggestion-header">
              <p className="eyebrow">Suggested Replies</p>
              <span>Click to draft</span>
            </div>
            <div className="suggestion-list">
              {replySuggestions.map((suggestion) => (
                <button
                  key={suggestion.title}
                  type="button"
                  className="suggestion-card"
                  onClick={() => setMessageDraft(suggestion.message)}
                >
                  <strong>{suggestion.title}</strong>
                  <span>{suggestion.message}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
        <div className="composer">
          <textarea
            value={messageDraft}
            onChange={(event) => setMessageDraft(event.target.value)}
            placeholder="Ask for supporting documents or confirm next actions"
          />
          <button type="button" onClick={onSend} disabled={busy}>
            Send Response
          </button>
        </div>
      </div>

      <div className="panel insights-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Decisioning</p>
            <h3>AI Summary</h3>
          </div>
          <button type="button" className="secondary-button" onClick={onRunAnalysis} disabled={busy}>
            Refresh Analysis
          </button>
        </div>

        {pipelineResult ? (
          <>
            <div className="summary-card">
              <p className="eyebrow">Summary</p>
              <p className="summary-text">{pipelineResult.summary}</p>
              <div className="pill-row">
                {pipelineResult.detected_needs.map((need) => (
                  <span key={need} className="pill">
                    {need}
                  </span>
                ))}
              </div>
            </div>

            {visibleAttributes.length > 0 ? (
              <div className="detail-grid">
                {visibleAttributes.map(([key, value]) => (
                  <div key={key} className="detail-tile">
                    <span>{key.replaceAll("_", " ")}</span>
                    <strong>{Array.isArray(value) ? value.join(", ") : String(value)}</strong>
                  </div>
                ))}
              </div>
            ) : null}

            <div className="recommendation-stack">
              {pipelineResult.recommendations.map((recommendation) => (
                <article key={recommendation.product} className="recommendation-card">
                  <div className="recommendation-head">
                    <h4>{recommendation.product}</h4>
                    <span className="score-badge">{recommendation.confidence.toFixed(2)}</span>
                  </div>
                  <div className="badge-row">
                    <span className={`status-badge ${statusClass(recommendation.eligibility)}`}>
                      {recommendation.eligibility}
                    </span>
                    <span className="ghost-badge">
                      {recommendation.assigned_agent.replaceAll("_", " ")}
                    </span>
                    {recommendation.retrieval_score ? (
                      <span className="ghost-badge">
                        Retrieval {recommendation.retrieval_score.toFixed(2)}
                      </span>
                    ) : null}
                  </div>
                  <dl className="recommendation-details">
                    <div>
                      <dt>Next Action</dt>
                      <dd>{recommendation.next_action}</dd>
                    </div>
                    <div>
                      <dt>Why</dt>
                      <dd>{recommendation.rationale}</dd>
                    </div>
                    <div>
                      <dt>Policy Match</dt>
                      <dd>{recommendation.retrieved_chunk || recommendation.policy_excerpt}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>

            <div className="section-divider" />
            <div className="task-header">
              <div>
                <p className="eyebrow">Execution</p>
                <h3>Task Board</h3>
              </div>
            </div>
            <div className="task-stack compact">
              {tasks.map((task) => (
                <article key={task.task_id} className="task-card compact">
                  <div>
                    <h4>{task.product}</h4>
                    <p>{task.action}</p>
                    <span className={`status-badge ${statusClass(task.status)}`}>{task.status}</span>
                  </div>
                  <div className="task-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => onTaskUpdate(task.task_id, "in_progress")}
                      disabled={busy || task.status !== "pending"}
                    >
                      Start
                    </button>
                    <button
                      type="button"
                      onClick={() => onTaskUpdate(task.task_id, "completed")}
                      disabled={busy || task.status === "completed"}
                    >
                      Complete
                    </button>
                  </div>
                </article>
              ))}
              {tasks.length === 0 ? <div className="empty-state">No tasks created yet.</div> : null}
            </div>
          </>
        ) : (
          <div className="empty-state">Run analysis to generate AI insights for this conversation.</div>
        )}
      </div>
    </section>
  );
}

function ClientPortal({
  selectedClient,
  conversation,
  pipelineResult,
  clientDraft,
  setClientDraft,
  onSend,
  busy,
}) {
  return (
    <section className="single-page">
      <div className="panel wide-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Client Portal</p>
            <h3>{selectedClient?.name || "Client"}</h3>
          </div>
        </div>

        {pipelineResult ? <div className="summary-banner">{pipelineResult.summary}</div> : null}

        <div className="chat-thread">
          {conversation.map((event) => (
            <article
              key={`${event.timestamp}-${event.actor}-${event.message}`}
              className={`message-card ${event.actor === "client" ? "client" : "agent"}`}
            >
              <div className="message-meta">{event.actor.replaceAll("_", " ")}</div>
              <p>{event.message}</p>
            </article>
          ))}
        </div>

        <div className="composer">
          <textarea
            value={clientDraft}
            onChange={(event) => setClientDraft(event.target.value)}
            placeholder="Share turnover, years in business, or additional financing needs"
          />
          <button type="button" onClick={onSend} disabled={busy}>
            Send Message
          </button>
        </div>
      </div>
    </section>
  );
}

function AdminPage({ conversationJson, setConversationJson, pipelineResult, onRunAnalysis, onReset, busy }) {
  return (
    <section className="single-page admin-layout">
      <div className="panel wide-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Admin</p>
            <h3>Demo Controls</h3>
          </div>
          <div className="action-row">
            <button type="button" className="secondary-button" onClick={onRunAnalysis} disabled={busy}>
              Run Pipeline
            </button>
            <button type="button" onClick={onReset} disabled={busy}>
              Reset Demo
            </button>
          </div>
        </div>

        <label className="json-label" htmlFor="conversation-json">
          Conversation JSON Preview
        </label>
        <textarea
          id="conversation-json"
          className="json-editor"
          value={conversationJson}
          onChange={(event) => setConversationJson(event.target.value)}
        />
      </div>

      <div className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Pipeline Output</p>
            <h3>Structured Result</h3>
          </div>
        </div>
        <pre className="result-viewer">
          {pipelineResult ? JSON.stringify(pipelineResult, null, 2) : "No pipeline result yet."}
        </pre>
      </div>
    </section>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{String(value)}</strong>
    </div>
  );
}

function statusClass(value) {
  const normalized = value.toLowerCase();
  if (normalized.includes("eligible") && !normalized.includes("not")) {
    return "good";
  }
  if (normalized.includes("not eligible")) {
    return "bad";
  }
  if (normalized.includes("completed")) {
    return "good";
  }
  if (normalized.includes("in_progress") || normalized.includes("in progress")) {
    return "progress";
  }
  return "warn";
}
