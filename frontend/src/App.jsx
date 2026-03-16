import { useEffect, useState } from "react";
import { api } from "./api";

const pages = ["Agent Dashboard", "Client Portal", "Policy Lab", "Admin Page", "POC Brief"];

export default function App() {
  const [page, setPage] = useState("Agent Dashboard");
  const [clients, setClients] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState("");
  const [selectedPolicyId, setSelectedPolicyId] = useState("");
  const [workspace, setWorkspace] = useState(null);
  const [messageDraft, setMessageDraft] = useState("");
  const [clientDraft, setClientDraft] = useState("");
  const [conversationJson, setConversationJson] = useState("[]");
  const [policyForm, setPolicyForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void refreshAll();
  }, []);

  useEffect(() => {
    if (!selectedClientId && clients.length > 0) {
      setSelectedClientId(clients[0].client_id);
    }
  }, [clients, selectedClientId]);

  useEffect(() => {
    if (!selectedPolicyId && policies.length > 0) {
      setSelectedPolicyId(policies[0].policy_id);
    }
  }, [policies, selectedPolicyId]);

  useEffect(() => {
    if (selectedClientId) {
      void refreshClient(selectedClientId);
    }
  }, [selectedClientId]);

  useEffect(() => {
    const selectedPolicy = policies.find((policy) => policy.policy_id === selectedPolicyId) || null;
    setPolicyForm(selectedPolicy ? toPolicyForm(selectedPolicy) : null);
  }, [policies, selectedPolicyId]);

  async function refreshAll() {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const [nextClients, nextPolicies] = await Promise.all([api.getClients(), api.getPolicies()]);
      setClients(nextClients);
      setPolicies(nextPolicies);
      if (!selectedClientId && nextClients.length > 0) {
        setSelectedClientId(nextClients[0].client_id);
      }
      if (!selectedPolicyId && nextPolicies.length > 0) {
        setSelectedPolicyId(nextPolicies[0].policy_id);
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
    setNotice("");
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
    setNotice("");
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
    setNotice("");
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
    setNotice("");
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

  async function handlePolicySave() {
    if (!selectedPolicyId || !policyForm) {
      return;
    }

    setBusy(true);
    setBusyLabel("Updating policy and RAG index...");
    setError("");
    setNotice("");
    try {
      const response = await api.updatePolicy(selectedPolicyId, {
        ...policyForm,
        title: policyForm.title.trim(),
        category: policyForm.category.trim(),
        policy_text: policyForm.policy_text.trim(),
        min_business_years: policyForm.min_business_years === "" ? null : policyForm.min_business_years,
        min_turnover: policyForm.min_turnover === "" ? null : policyForm.min_turnover,
        next_action: policyForm.next_action.trim(),
      });
      setPolicies((currentPolicies) =>
        currentPolicies.map((policy) =>
          policy.policy_id === response.policy.policy_id ? response.policy : policy,
        ),
      );
      setPolicyForm(toPolicyForm(response.policy));
      setNotice(response.message);
      if (selectedClientId) {
        const nextWorkspace = await api.runPipeline(selectedClientId);
        applyWorkspace(nextWorkspace);
      }
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
          <div className="topbar-meta">
            {clients.length > 0 ? (
              <label className="mobile-client-picker">
                <span>Client</span>
                <select
                  value={selectedClientId}
                  onChange={(event) => setSelectedClientId(event.target.value)}
                >
                  {clients.map((client) => (
                    <option key={client.client_id} value={client.client_id}>
                      {client.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {selectedClient ? (
              <div className="topbar-client">
                <span>{selectedClient.client_id}</span>
                <strong>{selectedClient.name}</strong>
              </div>
            ) : null}
          </div>
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
        {notice ? <div className="notice-banner">{notice}</div> : null}
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

        {!loading && page === "Policy Lab" ? (
          <PolicyLab
            policies={policies}
            selectedPolicyId={selectedPolicyId}
            setSelectedPolicyId={setSelectedPolicyId}
            policyForm={policyForm}
            setPolicyForm={setPolicyForm}
            onSave={handlePolicySave}
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

        {!loading && page === "POC Brief" ? <PocBrief /> : null}
      </main>
    </div>
  );
}

function toPolicyForm(policy) {
  return {
    title: policy.title || "",
    category: policy.category || "",
    policy_text: policy.policy_text || "",
    min_business_years: policy.min_business_years ?? "",
    min_turnover: policy.min_turnover ?? "",
    required_collateral: Boolean(policy.required_collateral),
    requires_import_export_activity: Boolean(policy.requires_import_export_activity),
    assigned_agent: policy.assigned_agent,
    next_action: policy.next_action || "",
  };
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

function PolicyLab({
  policies,
  selectedPolicyId,
  setSelectedPolicyId,
  policyForm,
  setPolicyForm,
  onSave,
  busy,
}) {
  const selectedPolicy = policies.find((policy) => policy.policy_id === selectedPolicyId) || null;

  function updateField(field, value) {
    setPolicyForm((current) => (current ? { ...current, [field]: value } : current));
  }

  return (
    <section className="single-page policy-layout">
      <div className="panel policy-sidebar-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">RAG Demo</p>
            <h3>Policy Library</h3>
          </div>
        </div>
        <div className="policy-list">
          {policies.map((policy) => (
            <button
              key={policy.policy_id}
              type="button"
              className={`policy-button ${policy.policy_id === selectedPolicyId ? "active" : ""}`}
              onClick={() => setSelectedPolicyId(policy.policy_id)}
            >
              <strong>{policy.product}</strong>
              <span>{policy.title}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="panel wide-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Policy Editor</p>
            <h3>{selectedPolicy?.product || "Select a policy"}</h3>
          </div>
          <button type="button" onClick={onSave} disabled={busy || !policyForm}>
            Save And Reindex
          </button>
        </div>

        {policyForm ? (
          <div className="policy-editor">
            <div className="policy-grid">
              <label>
                <span>Title</span>
                <input
                  value={policyForm.title}
                  onChange={(event) => updateField("title", event.target.value)}
                />
              </label>
              <label>
                <span>Category</span>
                <input
                  value={policyForm.category}
                  onChange={(event) => updateField("category", event.target.value)}
                />
              </label>
              <label>
                <span>Minimum Business Years</span>
                <input
                  type="number"
                  min="0"
                  value={policyForm.min_business_years}
                  onChange={(event) =>
                    updateField("min_business_years", event.target.value === "" ? "" : Number(event.target.value))
                  }
                />
              </label>
              <label>
                <span>Minimum Turnover</span>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  value={policyForm.min_turnover}
                  onChange={(event) =>
                    updateField("min_turnover", event.target.value === "" ? "" : Number(event.target.value))
                  }
                />
              </label>
              <label>
                <span>Assigned Agent</span>
                <select
                  value={policyForm.assigned_agent}
                  onChange={(event) => updateField("assigned_agent", event.target.value)}
                >
                  <option value="relationship_manager">Relationship Manager</option>
                  <option value="loan_specialist">Loan Specialist</option>
                  <option value="credit_card_specialist">Credit Card Specialist</option>
                  <option value="trade_finance_specialist">Trade Finance Specialist</option>
                </select>
              </label>
              <label>
                <span>Next Action</span>
                <input
                  value={policyForm.next_action}
                  onChange={(event) => updateField("next_action", event.target.value)}
                />
              </label>
            </div>

            <div className="toggle-row">
              <label className="toggle-card">
                <input
                  type="checkbox"
                  checked={policyForm.required_collateral}
                  onChange={(event) => updateField("required_collateral", event.target.checked)}
                />
                <span>Require collateral</span>
              </label>
              <label className="toggle-card">
                <input
                  type="checkbox"
                  checked={policyForm.requires_import_export_activity}
                  onChange={(event) =>
                    updateField("requires_import_export_activity", event.target.checked)
                  }
                />
                <span>Require import/export activity</span>
              </label>
            </div>

            <label className="policy-text-label">
              <span>Policy Document Text</span>
              <textarea
                className="policy-editor-textarea"
                value={policyForm.policy_text}
                onChange={(event) => updateField("policy_text", event.target.value)}
              />
            </label>

            <div className="policy-hint">
              Save updates the document, refreshes the RAG index, and reruns analysis for the selected client so
              retrieval changes are visible immediately.
            </div>
          </div>
        ) : (
          <div className="empty-state">Select a policy to edit the RAG source documents.</div>
        )}
      </div>
    </section>
  );
}

function PocBrief() {
  const appUrl = typeof window !== "undefined" ? window.location.origin : "https://deal-flow-ai-frontend.vercel.app";

  return (
    <section className="single-page">
      <div className="panel brief-hero stake-hero">
        <div className="stake-hero-grid">
          <div>
            <p className="eyebrow">Stakeholder Demo</p>
            <h3>DealFlow AI</h3>
            <p className="brief-intro">
              An AI-assisted relationship banking copilot that converts client conversations into product
              recommendations, eligibility decisions, and routed next steps.
            </p>
          </div>
          <div className="brief-url-card">
            <span>Live App URL</span>
            <strong>{appUrl}</strong>
          </div>
        </div>

        <div className="stake-pill-row">
          <span className="stake-pill">Conversation Intelligence</span>
          <span className="stake-pill">Policy-Aware Recommendations</span>
          <span className="stake-pill">Eligibility Checks</span>
          <span className="stake-pill">Task Routing</span>
        </div>
      </div>

      <div className="brief-grid">
        <div className="panel">
          <p className="eyebrow">The Problem</p>
          <h3>What We Are Solving</h3>
          <ul className="brief-list">
            <li>Relationship managers often have to manually interpret messy client conversations.</li>
            <li>Product matching and policy checks are slow and inconsistent.</li>
            <li>Follow-up actions are often delayed or routed manually.</li>
            <li>Client intent, eligibility, and next steps are rarely visible in one place.</li>
          </ul>
        </div>

        <div className="panel">
          <p className="eyebrow">The Outcome</p>
          <h3>What This POC Demonstrates</h3>
          <ul className="brief-list">
            <li>The app interprets the conversation and detects likely banking needs.</li>
            <li>It retrieves policy context before forming a recommendation.</li>
            <li>It checks whether the client is eligible, not eligible, or incomplete.</li>
            <li>It produces the next recommended action and routes a task to the right role.</li>
            <li>Teams can edit policy documents live in Policy Lab and immediately see RAG and eligibility updates.</li>
            <li>It suggests agent replies that reflect the latest conversation state.</li>
          </ul>
        </div>

        <div className="panel wide-brief-panel">
          <p className="eyebrow">Live Demo Story</p>
          <h3>Best Stakeholder Walkthrough</h3>
          <div className="storyline">
            <div className="story-step">
              <span>1</span>
              <div>
                <strong>Client expresses a financing need</strong>
                <p>Example: fleet expansion, export support, or business card limits.</p>
              </div>
            </div>
            <div className="story-step">
              <span>2</span>
              <div>
                <strong>DealFlow AI interprets the conversation</strong>
                <p>It detects likely products and retrieves the relevant policy match.</p>
              </div>
            </div>
            <div className="story-step">
              <span>3</span>
              <div>
                <strong>The app evaluates eligibility</strong>
                <p>It compares client facts such as turnover, business age, collateral, and trade activity.</p>
              </div>
            </div>
            <div className="story-step">
              <span>4</span>
              <div>
                <strong>Policy changes can be tested live</strong>
                <p>Using Policy Lab, a rule can be changed and the retrieved evidence updates on the next analysis run.</p>
              </div>
            </div>
            <div className="story-step">
              <span>5</span>
              <div>
                <strong>Next action is generated</strong>
                <p>Specialist routing or relationship-manager follow-up is created automatically.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="panel">
          <p className="eyebrow">What To Show</p>
          <h3>High-Impact Screens</h3>
          <ul className="brief-list">
            <li>
              <strong>Agent Dashboard</strong>: the main demo surface showing summary, recommendations, suggested
              replies, and task routing.
            </li>
            <li>
              <strong>Client Portal</strong>: demonstrates how client messages change the decisioning in real time.
            </li>
            <li>
              <strong>Policy Lab</strong>: demonstrates live policy editing, reindexing, and grounded retrieval updates.
            </li>
            <li>
              <strong>Admin Page</strong>: useful for resetting the demo and rerunning analysis.
            </li>
          </ul>
        </div>

        <div className="panel">
          <p className="eyebrow">Suggested Scenarios</p>
          <h3>Demo Prompts</h3>
          <ul className="brief-list">
            <li>
              <strong>Eligible case</strong>: “Our turnover is $8M, we have operated for 5 years, and the vehicles
              can be used as collateral.”
            </li>
            <li>
              <strong>Multi-product case</strong>: “We also support export routes to Europe and need help with
              trade-related payments.”
            </li>
            <li>
              <strong>Ineligible case</strong>: “Actually, we have only been operating for 1 year.”
            </li>
            <li>
              <strong>Criteria question</strong>: “What’s the criteria?”
            </li>
            <li>
              <strong>Live RAG change</strong>: change Vehicle Loan from 2 years to 1 year in Policy Lab, save, and rerun to show the retrieved policy text and eligibility result both update.
            </li>
          </ul>
        </div>

        <div className="panel">
          <p className="eyebrow">What Good Looks Like</p>
          <h3>Success Signals</h3>
          <ul className="brief-list">
            <li>The recommendation feels believable and grounded in policy.</li>
            <li>The eligibility result changes when the client shares new facts.</li>
            <li>The retrieved policy text changes when a policy document is edited in Policy Lab.</li>
            <li>The next action changes when the case becomes incomplete or ineligible.</li>
            <li>The suggested replies feel like a practical banker aid rather than a generic chatbot.</li>
          </ul>
        </div>

        <div className="panel">
          <p className="eyebrow">Current Scope</p>
          <h3>POC Boundaries</h3>
          <ul className="brief-list">
            <li>This is an internal proof of concept, not a production system.</li>
            <li>Application state is in-memory and may reset across cold starts or redeploys.</li>
            <li>Authentication and persistent storage are not yet included.</li>
            <li>The value being tested is workflow intelligence, not production hardening.</li>
          </ul>
        </div>
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
