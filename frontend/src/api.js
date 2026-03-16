const API_BASE = import.meta.env.VITE_API_BASE || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  getClients: () => request("/clients"),
  getWorkspace: (clientId) => request(`/clients/${clientId}/workspace`),
  getReplySuggestions: (clientId) => request(`/clients/${clientId}/reply-suggestions`),
  addMessage: (payload) =>
    request("/messages", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  runPipeline: (clientId) =>
    request("/pipeline/run", {
      method: "POST",
      body: JSON.stringify({ client_id: clientId }),
    }),
  updateTask: (taskId, status) =>
    request(`/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  resetDemo: () =>
    request("/admin/reset", {
      method: "POST",
    }),
};
