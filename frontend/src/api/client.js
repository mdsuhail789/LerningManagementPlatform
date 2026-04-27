const TOKEN_KEY = "learnflow_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 */
export async function api(path, options = {}) {
  const token = getToken();
  /** @type {Record<string, string>} */
  const headers = { ...(options.headers && typeof options.headers === "object" ? options.headers : {}) };
  if (!headers["Content-Type"] && options.body && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    if (!path.includes("/auth/login")) window.location.assign("/login");
    
    // Try to get backend error detail if available
    let detail = "Unauthorized";
    try {
      const text = await res.text();
      try {
        const j = JSON.parse(text);
        detail = j.detail || detail;
      } catch {
        detail = text || detail;
      }
    } catch {
      // fallback
    }
    throw new Error(detail);
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const text = await res.text();
      try {
        const j = JSON.parse(text);
        detail = j.detail || JSON.stringify(j);
      } catch {
        detail = text || res.statusText;
      }
    } catch {
      // fallback if even .text() fails
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }

  if (res.status === 204) return null;
  const ct = res.headers.get("content-type");
  if (ct && ct.includes("application/json")) return res.json();
  return res.text();
}
