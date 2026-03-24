"""
VulnTrack — Admin Landing Page
Run with:  streamlit run admin_landing.py
"""

import time
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

# ─────────────────────────────────────────
# Page config (MUST be first Streamlit call)
# ─────────────────────────────────────────
st.set_page_config(
    page_title="VulnTrack · Admin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# Session State bootstrap
# ─────────────────────────────────────────
for key, default in {
    "token": None,
    "username": None,
    "role": None,
    "notif_open": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────
# Custom CSS — dark, sharp, professional
# ─────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif;
        background-color: #0a0c10;
        color: #e2e8f0;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0f1117;
        border-right: 1px solid #1e2530;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #94a3b8 !important;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 18px 20px !important;
        transition: border-color 0.2s;
    }
    [data-testid="metric-container"]:hover { border-color: #3b82f6; }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-size: 2rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── Section headers ── */
    h2, h3 { font-family: 'Syne', sans-serif !important; font-weight: 800; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid #1e2530;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #64748b !important;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background: #1e2530 !important;
        color: #60a5fa !important;
        border-bottom: 2px solid #3b82f6 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: #1e3a5f;
        color: #93c5fd;
        border: 1px solid #2563eb;
        border-radius: 6px;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
        padding: 6px 18px;
        transition: all 0.15s;
    }
    .stButton > button:hover {
        background: #2563eb;
        color: #ffffff;
    }

    /* ── Notification badge ── */
    .notif-badge {
        display: inline-block;
        background: #ef4444;
        color: white;
        border-radius: 50%;
        width: 18px; height: 18px;
        font-size: 0.65rem;
        font-weight: 700;
        text-align: center;
        line-height: 18px;
        margin-left: 4px;
        vertical-align: middle;
    }
    .notif-item {
        background: #111827;
        border-left: 3px solid #3b82f6;
        border-radius: 0 6px 6px 0;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 0.82rem;
    }
    .notif-item.unread { border-left-color: #f59e0b; }
    .notif-item .ts {
        color: #475569;
        font-size: 0.7rem;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 3px;
    }

    /* ── Severity pills ── */
    .pill {
        display: inline-block;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.7rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
    }
    .pill-critical { background:#450a0a; color:#fca5a5; }
    .pill-high     { background:#431407; color:#fdba74; }
    .pill-medium   { background:#422006; color:#fde68a; }
    .pill-low      { background:#052e16; color:#86efac; }
    .pill-info     { background:#0c1a2e; color:#93c5fd; }

    /* ── Dataframe ── */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: #111827;
        border: 1px solid #1e2530;
        border-radius: 8px;
    }

    /* ── Input fields ── */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: #0f1117 !important;
        border-color: #1e2530 !important;
        color: #e2e8f0 !important;
        border-radius: 6px;
    }

    /* ── Divider ── */
    hr { border-color: #1e2530; }

    /* ── Top bar ── */
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0 18px 0;
        border-bottom: 1px solid #1e2530;
        margin-bottom: 24px;
    }
    .topbar-logo {
        font-size: 1.5rem;
        font-weight: 800;
        color: #f1f5f9;
        letter-spacing: -0.5px;
    }
    .topbar-logo span { color: #3b82f6; }
    .topbar-user {
        font-size: 0.75rem;
        color: #475569;
        font-family: 'JetBrains Mono', monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────
# Helper: authenticated API calls
# ─────────────────────────────────────────
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_get(path: str, **params) -> requests.Response:
    return requests.get(f"{API_URL}{path}", headers=auth_headers(), params=params, timeout=10)


def api_post(path: str, json: dict | None = None, **params) -> requests.Response:
    return requests.post(f"{API_URL}{path}", headers=auth_headers(), json=json, params=params, timeout=10)


# ─────────────────────────────────────────
# Severity colour map for Plotly
# ─────────────────────────────────────────
SEV_COLOR: dict[str, str] = {
    "critical": "#ef4444",
    "high":     "#f97316",
    "medium":   "#eab308",
    "low":      "#22c55e",
    "info":     "#3b82f6",
}

STATUS_COLOR: dict[str, str] = {
    "open":        "#ef4444",
    "in_progress": "#f97316",
    "resolved":    "#22c55e",
    "closed":      "#64748b",
    "wont_fix":    "#a855f7",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#94a3b8",
    font_family="Syne",
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font_color="#94a3b8",
    ),
)


# ─────────────────────────────────────────
# Fetch dashboard data from API
# ─────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def fetch_dashboard(
    template: str | None = None,
    application: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    module: str | None = None,
    assigned_to: str | None = None,
    _token: str = "",          # cache-busting arg
) -> dict:
    payload = {k: v for k, v in {
        "template": template,
        "application": application,
        "severity": severity,
        "status": status,
        "module": module,
        "assigned_to": assigned_to,
    }.items() if v}

    resp = requests.post(
        f"{API_URL}/admin/dashboard",
        headers={"Authorization": f"Bearer {_token}"},
        json=payload,
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json()
    return {}


@st.cache_data(ttl=15, show_spinner=False)
def fetch_vulns(_token: str = "") -> pd.DataFrame:
    resp = requests.get(
        f"{API_URL}/vulnerabilities",
        headers={"Authorization": f"Bearer {_token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return pd.DataFrame(resp.json())
    return pd.DataFrame()


@st.cache_data(ttl=10, show_spinner=False)
def fetch_notifications(_token: str = "") -> dict:
    resp = requests.get(
        f"{API_URL}/admin/notifications",
        headers={"Authorization": f"Bearer {_token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json()
    return {"notifications": [], "unread_count": 0}


# ─────────────────────────────────────────
# ── LOGIN GATE ──
# ─────────────────────────────────────────
if not st.session_state.token:
    st.markdown(
        """
        <div style='max-width:380px;margin:80px auto 0;text-align:center;'>
          <div style='font-size:2.2rem;font-weight:800;letter-spacing:-1px;margin-bottom:4px;'>
            🛡️ <span style='color:#3b82f6;'>Vuln</span>Track
          </div>
          <div style='color:#475569;font-size:0.82rem;margin-bottom:32px;
                      font-family:"JetBrains Mono",monospace;'>
            ADMIN CONSOLE
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In", use_container_width=True):
            resp = requests.post(
                f"{API_URL}/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data["role"] != "admin":
                    st.error("This portal is for admins only.")
                else:
                    st.session_state.token    = data["access_token"]
                    st.session_state.username = username
                    st.session_state.role     = data["role"]
                    st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()


# ─────────────────────────────────────────
# ── MAIN ADMIN LAYOUT ──
# ─────────────────────────────────────────

# ── Sidebar filters ──────────────────────
with st.sidebar:
    st.markdown(
        "<div style='font-size:1.1rem;font-weight:800;padding:12px 0 4px;color:#f1f5f9;'>"
        "🛡️ <span style='color:#3b82f6;'>Vuln</span>Track</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:0.72rem;color:#475569;font-family:JetBrains Mono,monospace;"
        f"margin-bottom:20px;'>admin / {st.session_state.username}</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("**Dashboard Filters**")

    # Dynamic filter options pulled from live data
    df_all = fetch_vulns(_token=st.session_state.token)

    def opts(col: str) -> list[str]:
        if df_all.empty or col not in df_all.columns:
            return []
        return sorted(df_all[col].dropna().unique().tolist())

    f_template    = st.selectbox("Template",    ["All"] + opts("template"))
    f_application = st.selectbox("Application", ["All"] + opts("application"))
    f_module      = st.selectbox("Module",      ["All"] + opts("module"))
    f_severity    = st.selectbox("Severity",    ["All", "critical", "high", "medium", "low", "info"])
    f_status      = st.selectbox("Status",      ["All", "open", "in_progress", "resolved", "closed", "wont_fix"])
    f_assigned    = st.text_input("Assigned to (username)")

    st.divider()
    if st.button("🔄  Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("🚪  Logout", use_container_width=True):
        for k in ["token", "username", "role"]:
            st.session_state[k] = None
        st.rerun()


# Helper: convert "All" → None for API
def _f(val: str) -> str | None:
    return None if val == "All" or not val else val


# Fetch dashboard
dash = fetch_dashboard(
    template=_f(f_template),
    application=_f(f_application),
    severity=_f(f_severity),
    status=_f(f_status),
    module=_f(f_module),
    assigned_to=_f(f_assigned) or None,
    _token=st.session_state.token,
)

notif_data = fetch_notifications(_token=st.session_state.token)
unread = notif_data.get("unread_count", 0)

# ── Top bar ──────────────────────────────
badge = f'<span class="notif-badge">{unread}</span>' if unread else ""
st.markdown(
    f"""
    <div class="topbar">
      <div class="topbar-logo">🛡️ <span>Vuln</span>Track <span style='color:#475569;font-size:0.9rem;font-weight:400;'> / Admin Dashboard</span></div>
      <div class="topbar-user">
        {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")} &nbsp;|&nbsp;
        🔔 Notifications {badge}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────
tab_dash, tab_vulns, tab_notif, tab_mgmt = st.tabs([
    "📊  Overview",
    "🐛  Vulnerabilities",
    "🔔  Notifications",
    "⚙️  Management",
])


# ═══════════════════════════════════════════
# TAB 1 — Overview Dashboard
# ═══════════════════════════════════════════
with tab_dash:
    if not dash:
        st.warning("Unable to load dashboard. Check API connection.")
    else:
        # ── KPI row ──────────────────────────────
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total",      dash.get("total_vulnerabilities", 0))
        c2.metric("Open",       dash.get("open_count", 0),    delta=None)
        c3.metric("Resolved",   dash.get("resolved_count", 0))
        c4.metric("Critical",   dash.get("critical_count", 0))
        c5.metric("Unread Alerts", unread)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 1: Severity donut + Status bar ───
        row1_l, row1_r = st.columns(2)

        with row1_l:
            st.markdown("##### Severity Distribution")
            sev_data = dash.get("by_severity", {})
            if sev_data:
                fig = go.Figure(go.Pie(
                    labels=list(sev_data.keys()),
                    values=list(sev_data.values()),
                    hole=0.55,
                    marker_colors=[SEV_COLOR.get(k, "#64748b") for k in sev_data],
                    textinfo="label+percent",
                    textfont_color="#e2e8f0",
                ))
                fig.update_layout(**PLOTLY_LAYOUT, height=280)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data")

        with row1_r:
            st.markdown("##### Status Breakdown")
            st_data = dash.get("by_status", {})
            if st_data:
                fig = go.Figure(go.Bar(
                    x=list(st_data.keys()),
                    y=list(st_data.values()),
                    marker_color=[STATUS_COLOR.get(k, "#64748b") for k in st_data],
                    text=list(st_data.values()),
                    textposition="outside",
                    textfont_color="#e2e8f0",
                ))
                fig.update_layout(**PLOTLY_LAYOUT, height=280,
                                  xaxis=dict(tickfont_color="#64748b"),
                                  yaxis=dict(tickfont_color="#64748b", showgrid=False))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data")

        # ── Row 2: By Application + By Template ──
        row2_l, row2_r = st.columns(2)

        with row2_l:
            st.markdown("##### Vulnerabilities by Application")
            app_data = dash.get("by_application", {})
            if app_data:
                fig = px.bar(
                    x=list(app_data.values()),
                    y=list(app_data.keys()),
                    orientation="h",
                    color=list(app_data.values()),
                    color_continuous_scale=["#1e3a5f", "#3b82f6", "#93c5fd"],
                    labels={"x": "Count", "y": ""},
                )
                fig.update_layout(**PLOTLY_LAYOUT, height=280,
                                  coloraxis_showscale=False,
                                  yaxis=dict(tickfont_color="#94a3b8"),
                                  xaxis=dict(tickfont_color="#64748b"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data")

        with row2_r:
            st.markdown("##### Vulnerabilities by Template")
            tpl_data = dash.get("by_template", {})
            if tpl_data:
                fig = px.bar(
                    x=list(tpl_data.values()),
                    y=list(tpl_data.keys()),
                    orientation="h",
                    color=list(tpl_data.values()),
                    color_continuous_scale=["#1a1a2e", "#7c3aed", "#c4b5fd"],
                    labels={"x": "Count", "y": ""},
                )
                fig.update_layout(**PLOTLY_LAYOUT, height=280,
                                  coloraxis_showscale=False,
                                  yaxis=dict(tickfont_color="#94a3b8"),
                                  xaxis=dict(tickfont_color="#64748b"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data")

        # ── Row 3: By Module heatmap-style ───────
        mod_data = dash.get("by_module", {})
        if mod_data:
            st.markdown("##### Vulnerabilities by Module")
            fig = px.treemap(
                names=list(mod_data.keys()),
                parents=["" for _ in mod_data],
                values=list(mod_data.values()),
                color=list(mod_data.values()),
                color_continuous_scale=["#0f172a", "#1d4ed8", "#60a5fa"],
            )
            fig.update_layout(**PLOTLY_LAYOUT, height=220, coloraxis_showscale=False)
            fig.update_traces(textfont_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True)

        # ── Recent activity ───────────────────────
        st.markdown("##### ⏱ Recent Vulnerabilities")
        recent = dash.get("recent", [])
        if recent:
            recent_df = pd.DataFrame(recent)
            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "severity": st.column_config.TextColumn("Severity"),
                    "status":   st.column_config.TextColumn("Status"),
                    "created_at": st.column_config.TextColumn("Created"),
                },
            )
        else:
            st.info("No recent vulnerabilities")


# ═══════════════════════════════════════════
# TAB 2 — Full Vulnerabilities Table
# ═══════════════════════════════════════════
with tab_vulns:
    df = fetch_vulns(_token=st.session_state.token)

    if df.empty:
        st.info("No vulnerabilities found.")
    else:
        # Apply sidebar filters locally too
        if _f(f_template):
            df = df[df["template"] == f_template]
        if _f(f_application):
            df = df[df["application"] == f_application]
        if _f(f_module):
            df = df[df["module"] == f_module]
        if _f(f_severity):
            df = df[df["severity"] == f_severity]
        if _f(f_status):
            df = df[df["status"] == f_status]
        if _f(f_assigned):
            df = df[df["assigned_to"] == f_assigned]

        st.markdown(f"**{len(df)} vulnerabilities** matching current filters")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id":          st.column_config.NumberColumn("ID", width="small"),
                "title":       st.column_config.TextColumn("Title", width="large"),
                "severity":    st.column_config.TextColumn("Severity"),
                "status":      st.column_config.TextColumn("Status"),
                "template":    st.column_config.TextColumn("Template"),
                "application": st.column_config.TextColumn("Application"),
                "module":      st.column_config.TextColumn("Module"),
                "assigned_to": st.column_config.TextColumn("Assigned To"),
                "created_at":  st.column_config.TextColumn("Created"),
            },
        )

        # ── Add vulnerability ─────────────────────
        st.divider()
        with st.expander("➕ Add New Vulnerability"):
            with st.form("add_vuln_form"):
                col_a, col_b = st.columns(2)
                v_id    = col_a.number_input("ID", min_value=1, step=1)
                v_title = col_b.text_input("Title")

                col_c, col_d, col_e = st.columns(3)
                v_sev  = col_c.selectbox("Severity", ["critical","high","medium","low","info"])
                v_stat = col_d.selectbox("Status",   ["open","in_progress","resolved","closed","wont_fix"])
                v_asgn = col_e.text_input("Assigned To")

                col_f, col_g, col_h = st.columns(3)
                v_tpl  = col_f.text_input("Template")
                v_app  = col_g.text_input("Application")
                v_mod  = col_h.text_input("Module")

                v_desc = st.text_area("Description")

                if st.form_submit_button("Add Vulnerability", use_container_width=True):
                    payload = {
                        "id": int(v_id), "title": v_title, "severity": v_sev,
                        "status": v_stat, "description": v_desc,
                        "assigned_to": v_asgn or None,
                        "template": v_tpl, "application": v_app,
                        "module": v_mod or None,
                    }
                    resp = api_post("/vulnerabilities", json=payload)
                    if resp.status_code == 200:
                        st.success("Vulnerability added ✓")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Error"))

        # ── Update vulnerability ──────────────────
        with st.expander("✏️ Update Vulnerability Status"):
            with st.form("update_vuln_form"):
                upd_id     = st.number_input("Vulnerability ID", min_value=1, step=1)
                upd_status = st.selectbox("New Status", ["open","in_progress","resolved","closed","wont_fix"])
                upd_sev    = st.selectbox("New Severity (optional)", ["— keep —","critical","high","medium","low","info"])
                if st.form_submit_button("Update", use_container_width=True):
                    body: dict = {"status": upd_status}
                    if upd_sev != "— keep —":
                        body["severity"] = upd_sev
                    resp = api_post(f"/vulnerabilities/{int(upd_id)}", json=body)
                    if resp.status_code == 200:
                        st.success("Updated ✓")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Error"))


# ═══════════════════════════════════════════
# TAB 3 — Notifications
# ═══════════════════════════════════════════
with tab_notif:
    col_h, col_btn = st.columns([4, 1])
    # ↓ both replacement lines must also have 4 spaces
    notif_badge_html = f'<span class="notif-badge">{unread}</span>' if unread else ""
    col_h.markdown(f"### 🔔 Notifications &nbsp; {notif_badge_html}", unsafe_allow_html=True)
    if col_btn.button("Mark all read"):
        api_post("/admin/notifications/mark-read")
        st.cache_data.clear()
        st.success("All marked as read")
        time.sleep(0.5)
        st.rerun()

    notifications = notif_data.get("notifications", [])
    if not notifications:
        st.info("No notifications yet.")
    else:
        for n in notifications:
            is_unread = not n.get("read", True)
            cls = "notif-item unread" if is_unread else "notif-item"
            event_icon = {
                "created":          "🆕",
                "status_changed":   "🔄",
                "severity_changed": "⚠️",
                "assigned":         "👤",
                "resolved":         "✅",
            }.get(n.get("event_type", ""), "📌")

            ts = n.get("timestamp", "")[:16].replace("T", " ")
            st.markdown(
                f"""
                <div class="{cls}">
                  {event_icon} <strong>{n.get('vuln_title','—')}</strong>
                  <span style='color:#475569;font-size:0.72rem;margin-left:8px;'>#{n.get('vuln_id','?')}</span>
                  <br>
                  {n.get('message','')}
                  <div class="ts">by {n.get('triggered_by','?')} · {ts} UTC</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════
# TAB 4 — User Management
# ═══════════════════════════════════════════
with tab_mgmt:
    st.markdown("### ⚙️ User Management")

    m1, m2 = st.columns(2)

    with m1:
        with st.expander("➕ Create User"):
            with st.form("create_user"):
                nu_user = st.text_input("Username")
                nu_pass = st.text_input("Password", type="password")
                nu_role = st.selectbox("Role", ["user", "admin"])
                if st.form_submit_button("Create", use_container_width=True):
                    resp = api_post(
                        "/admin/create-user",
                        json={"username": nu_user, "password": nu_pass, "role": nu_role},
                    )
                    if resp.status_code == 200:
                        st.success("User created ✓")
                    else:
                        st.error(resp.json().get("detail", "Error"))

        with st.expander("⬆️ Promote to Admin"):
            with st.form("promote_form"):
                promo_id = st.text_input("Username to promote")
                if st.form_submit_button("Promote", use_container_width=True):
                    resp = api_post(f"/admin/promote/{promo_id}")
                    if resp.status_code == 200:
                        st.success("Promoted ✓")
                    else:
                        st.error(resp.json().get("detail", "Error"))

    with m2:
        with st.expander("🔑 Change Password"):
            with st.form("change_pwd"):
                cp_target = st.text_input("Target Username")
                cp_newpwd = st.text_input("New Password", type="password")
                if st.form_submit_button("Update", use_container_width=True):
                    resp = api_post(
                        "/admin/change-password",
                        json={"target_username": cp_target, "new_password": cp_newpwd},
                    )
                    if resp.status_code == 200:
                        st.success("Password updated ✓")
                    else:
                        st.error(resp.json().get("detail", "Error"))

        with st.expander("🗑️ Delete User"):
            with st.form("delete_user"):
                del_id = st.text_input("Username to delete")
                confirm = st.checkbox("I confirm deletion")
                if st.form_submit_button("Delete", use_container_width=True):
                    if not confirm:
                        st.warning("Please confirm deletion first.")
                    else:
                        resp = requests.delete(
                            f"{API_URL}/admin/delete-user/{del_id}",
                            headers=auth_headers(),
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            st.success("User deleted ✓")
                        else:
                            st.error(resp.json().get("detail", "Error"))