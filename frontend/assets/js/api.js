// Thin fetch wrapper around the Flask REST API. The frontend is plain
// HTML/CSS/JS; all auth, ML classification, and persistence happen in
// the Python backend. The JWT issued at login/register is kept in
// localStorage and attached to every authenticated request.

const Auth = {
  getToken() { return localStorage.getItem("token"); },
  setSession(token, user) {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
  },
  getUser() {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  },
  isLoggedIn() { return !!this.getToken(); },
  isAdmin() {
    const u = this.getUser();
    return !!u && u.role === "admin";
  },
  logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = (window.SITE_ROOT || "") + "login.html";
  },
  requireAuth() {
    if (!this.isLoggedIn()) window.location.href = (window.SITE_ROOT || "") + "login.html";
  },
  requireAdmin() {
    if (!this.isLoggedIn() || !this.isAdmin()) window.location.href = (window.SITE_ROOT || "") + "dashboard.html";
  },
  redirectIfLoggedIn() {
    if (this.isLoggedIn()) window.location.href = (window.SITE_ROOT || "") + "dashboard.html";
  },
};

async function apiRequest(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = Auth.getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  let res;
  try {
    res = await fetch(window.API_BASE_URL + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error("Could not reach the server. Is the Flask backend running on port 5000?");
  }

  let data = null;
  const text = await res.text();
  if (text) {
    try { data = JSON.parse(text); } catch (e) { data = null; }
  }

  if (res.status === 401 && path !== "/auth/login") {
    Auth.logout();
    return;
  }

  if (!res.ok) {
    const message = (data && data.error) ? data.error : `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

const Api = {
  get: (path) => apiRequest("GET", path),
  post: (path, body) => apiRequest("POST", path, body),
  put: (path, body) => apiRequest("PUT", path, body),
  patch: (path, body) => apiRequest("PATCH", path, body),
  del: (path) => apiRequest("DELETE", path),
};

function showAlert(containerEl, message, type) {
  containerEl.innerHTML = `<div class="alert ${type}">${escapeHtml(message)}</div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}

function severityBadgeClass(level) {
  return "badge " + String(level).replace(/\s+/g, "");
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleString(undefined, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

// Renders the shared navbar into #navbar-placeholder based on auth state.
// Pages under admin/ set window.SITE_ROOT = "../" before this runs so
// links resolve correctly from the subfolder.
function renderNav() {
  const el = document.getElementById("navbar-placeholder");
  if (!el) return;
  const loggedIn = Auth.isLoggedIn();
  const isAdmin = Auth.isAdmin();
  const user = Auth.getUser();
  const root = window.SITE_ROOT || "";

  let links = "";
  if (loggedIn) {
    links += `<a href="${root}dashboard.html">Dashboard</a>`;
    links += `<a href="${root}assessment.html">Assessment</a>`;
    links += `<a href="${root}progress.html">Progress</a>`;
    links += `<a href="${root}knowledge.html">Knowledge Base</a>`;
    links += `<a href="${root}feedback.html">Feedback</a>`;
    links += `<a href="${root}profile.html">Profile</a>`;
    if (isAdmin) links += `<a href="${root}admin/index.html">Admin</a>`;
    links += `<a href="#" id="logout-link">Logout (${escapeHtml(user ? user.username : "")})</a>`;
  } else {
    links += `<a href="${root}login.html">Login</a>`;
    links += `<a href="${root}register.html">Register</a>`;
  }

  el.innerHTML = `
    <div class="navbar">
      <a class="brand" href="${loggedIn ? root + "dashboard.html" : root + "index.html"}">
        <span class="logo-mark">&#129504;</span> Intelligent Stress Support
      </a>
      <nav>${links}</nav>
    </div>`;

  const logoutLink = document.getElementById("logout-link");
  if (logoutLink) {
    logoutLink.addEventListener("click", (e) => { e.preventDefault(); Auth.logout(); });
  }
}

// Renders the shared, professional multi-column footer into
// #footer-placeholder. Same SITE_ROOT convention as renderNav.
function renderFooter() {
  const el = document.getElementById("footer-placeholder");
  if (!el) return;
  const root = window.SITE_ROOT || "";
  const loggedIn = Auth.isLoggedIn();
  const year = new Date().getFullYear();

  el.innerHTML = `
    <footer class="site-footer">
      <div class="footer-inner">
        <div>
          <div class="footer-brand"><span class="logo-mark">&#129504;</span> Intelligent Stress Support</div>
          <p>A Decision Support System that combines a validated stress assessment, a machine-learning
            stress classifier, and personalized intervention recommendations to support proactive,
            accessible stress management.</p>
        </div>
        <div>
          <h4>Platform</h4>
          <ul>
            <li><a href="${root}${loggedIn ? "dashboard.html" : "index.html"}">${loggedIn ? "Dashboard" : "Home"}</a></li>
            <li><a href="${root}assessment.html">Stress Assessment</a></li>
            <li><a href="${root}progress.html">Progress Tracking</a></li>
            <li><a href="${root}knowledge.html">Knowledge Base</a></li>
          </ul>
        </div>
        <div>
          <h4>Account</h4>
          <ul>
            ${loggedIn
              ? `<li><a href="${root}profile.html">Profile</a></li><li><a href="${root}feedback.html">Feedback</a></li><li><a href="#" id="footer-logout-link">Logout</a></li>`
              : `<li><a href="${root}login.html">Login</a></li><li><a href="${root}register.html">Register</a></li>`}
          </ul>
        </div>
        <div>
          <h4>About</h4>
          <p>Built as part of a Technical Research Project: "An Intelligent Support Framework for Stress
            Management: A Decision Support System Approach." DSS principles (Power, 2002) combined with
            AI/ML techniques (Russell &amp; Norvig, 2021).</p>
        </div>
      </div>
      <div class="footer-bottom">&copy; ${year} Intelligent Support Framework for Stress Management &mdash; DSS + AI Research Project</div>
    </footer>`;

  const footerLogout = document.getElementById("footer-logout-link");
  if (footerLogout) {
    footerLogout.addEventListener("click", (e) => { e.preventDefault(); Auth.logout(); });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  renderNav();
  renderFooter();
});
