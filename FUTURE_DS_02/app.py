import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

REPO_URL = "https://github.com/priyam-10/Customer-Retention-Churn-Analysis-Dashboard"
DATA_URL = ("https://raw.githubusercontent.com/priyam-10/Customer-Retention-Churn-Analysis-Dashboard/"
            "main/FUTURE_DS_02/Dataset/WA_Fn-UseC_-Telco-Customer-Churn.csv")

BAR = "#5b3b91"
INK = "#28252d"

st.set_page_config(page_title="Customer Retention & Churn Analysis Dashboard",
                   page_icon="💜", layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(135deg,#180d45 0%,#2d1063 55%,#130b39 100%); }}
.block-container {{ padding: 1rem 1.25rem; max-width: 1700px; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.hero {{ background:#39245f; border-radius:12px; padding:16px 22px; color:#fff;
        display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:12px; }}
.hero h1 {{ color:#fff !important; font-size:32px; font-weight:800; margin:0; padding:0; }}
.hero p {{ color:#fff; font-size:16px; font-weight:600; margin:4px 0 0; }}
.hero a {{ background:#fff; color:{INK} !important; border:2px solid {INK}; border-radius:8px;
          padding:8px 16px; font-weight:700; text-decoration:none; }}
.kpi {{ background:#fff; border-radius:12px; padding:14px 18px; display:flex; justify-content:space-between;
       align-items:center; margin-bottom:12px; }}
.kpi .ic {{ font-size:38px; }}
.kpi .lb {{ color:{INK}; font-size:14px; font-weight:600; text-align:right; }}
.kpi .vl {{ color:{INK}; font-size:32px; font-weight:800; text-align:right; }}
div[data-testid="stPlotlyChart"] {{ background:#fff; border-radius:12px; padding:6px; }}
section[data-testid="stSidebar"] {{ background:#ffffff; }}
section[data-testid="stSidebar"] * {{ color:{INK} !important; }}
/* ---- Dropdowns: always white with dark text (works even in Streamlit dark mode) ---- */
[data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stSelectbox"] div[data-baseweb="select"] div,
[data-testid="stSelectbox"] div:not([data-testid="stWidgetLabel"]):not([data-testid="stWidgetLabel"] *) {{
  background-color:#ffffff !important; color:{INK} !important; }}
[data-testid="stSelectbox"] > div > div:last-child, [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
  border:1px solid #c9c3d6 !important; border-radius:8px !important; }}
[data-testid="stSelectbox"] div[data-baseweb="select"] span,
[data-testid="stSelectbox"] div[data-baseweb="select"] input,
[data-testid="stSelectbox"] div, [data-testid="stSelectbox"] span, [data-testid="stSelectbox"] input {{
  color:{INK} !important; -webkit-text-fill-color:{INK} !important; opacity:1 !important; }}
[data-testid="stSelectbox"] svg {{ fill:{INK} !important; color:{INK} !important; }}
div[data-baseweb="popover"], div[data-baseweb="popover"] > div, div[data-baseweb="menu"],
div[data-baseweb="popover"] ul, ul[role="listbox"], [data-testid="stSelectboxVirtualDropdown"] {{
  background-color:#ffffff !important; }}
ul[role="listbox"] li, [role="option"], [role="option"] * {{
  background-color:#ffffff !important; color:{INK} !important; }}
ul[role="listbox"] li:hover, [role="option"]:hover, [role="option"]:hover *,
[role="option"][aria-selected="true"], [role="option"][aria-selected="true"] * {{
  background-color:#ece6f6 !important; }}
.foot {{ color:#fff; text-align:center; margin-top:10px; }}
.foot a {{ color:#fff !important; text-decoration:underline; }}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner="Loading data...")
def load():
    df = pd.read_csv(DATA_URL)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"])
    df["SeniorCitizen"] = df["SeniorCitizen"].map({1: "Yes", 0: "No"})
    df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)
    df["TenureGroup"] = pd.cut(df["tenure"], [-1, 12, 24, 48, 1000],
                               labels=["0-12 Months", "13-24 Months", "25-48 Months", "49+ Months"])
    return df


df = load()

# ---------- Sidebar filters ----------
FILTERS = {"Contract": "Contract Type", "InternetService": "Internet Services",
           "PaymentMethod": "Payment Method", "gender": "Gender", "SeniorCitizen": "SeniorCitizen",
           "PhoneService": "Phone Service", "Partner": "Partner", "Dependents": "Dependents"}
st.sidebar.markdown("### Filters")
d = df.copy()
for col, label in FILTERS.items():
    choice = st.sidebar.selectbox(label, ["All"] + sorted(df[col].unique().tolist()), key=col)
    if choice != "All":
        d = d[d[col] == choice]
st.sidebar.markdown(f"[📂 GitHub repository]({REPO_URL})")

# ---------- Header ----------
st.markdown(f"""
<div class="hero">
  <div><h1>👥 Customer Retention &amp; Churn Analysis Dashboard</h1>
  <p>Customer Segmentation, Retention Trends &amp; Churn Driver Analysis</p></div>
  <a href="{REPO_URL}" target="_blank">View on GitHub →</a>
</div>""", unsafe_allow_html=True)

if d.empty:
    st.warning("No customers match these filters.")
    st.stop()


def k(n):
    return f"{n/1000:.2f}K" if n >= 1000 else f"{n:.0f}"


churned = int(d["ChurnFlag"].sum())
kpis = [("👥", "Total Customers", k(len(d))), ("🚫", "Churned Customers", k(churned)),
        ("📈", "Retained Customers", k(len(d) - churned)), ("⏱️", "Avg Tenure", f"{d['tenure'].mean():.2f}"),
        ("💰", "Avg Total Charges", f"${k(d['TotalCharges'].mean())}")]
for c, (ic, lb, vl) in zip(st.columns(5), kpis):
    c.markdown(f'<div class="kpi"><span class="ic">{ic}</span><div><div class="lb">{lb}</div>'
               f'<div class="vl">{vl}</div></div></div>', unsafe_allow_html=True)


# ---------- Chart helpers (Power BI look) ----------
SHORT = {"Electronic check": "Electronic che...", "Bank transfer (automatic)": "Bank transfer ...",
         "Credit card (automatic)": "Credit card (a...", "No internet service": "No inte..."}


def rate(col, order=None):
    r = (d.groupby(col, observed=True)["ChurnFlag"].mean() * 100).round(2)
    r = r.reindex([o for o in order if o in r.index]) if order else r.sort_values(ascending=False)
    return [SHORT.get(str(i), str(i)) for i in r.index], r.values.tolist()


def style(fig, title, h):
    fig.update_layout(template="plotly_white", height=h, paper_bgcolor="white", plot_bgcolor="white",
                      title=dict(text=title, x=0.01, y=0.96, font=dict(color=INK, size=18)),
                      font=dict(color=INK, size=13), margin=dict(l=10, r=70, t=55, b=10), showlegend=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False, title=None,
                     tickfont=dict(color="#4a4650", size=13), automargin=True)
    fig.update_yaxes(showgrid=False, zeroline=False, showline=False, title=None,
                     tickfont=dict(color="#4a4650", size=13), automargin=True)
    return fig


def vbar(col, title, order, h=250, width=0.75):
    x, y = rate(col, order)
    fig = go.Figure(go.Bar(x=x, y=y, marker_color=BAR, width=width, text=[f"{v:.2f}%" for v in y],
                           textposition="outside", textfont=dict(color="#4a4650", size=13), cliponaxis=False))
    fig.update_yaxes(visible=False, range=[0, max(y + [1]) * 1.25])
    return style(fig, title, h)


def hbar(col, title, h=300, fmt=lambda v: f"{v:.2f}%", data=None):
    x, y = data if data else rate(col)
    fig = go.Figure(go.Bar(x=y, y=x, orientation="h", marker_color=BAR, width=0.75,
                           text=[fmt(v) for v in y], textposition="outside",
                           textfont=dict(color="#4a4650", size=13), cliponaxis=False))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(visible=False, range=[0, max(y + [1]) * 1.15])
    return style(fig, title, h)


cfg = {"displayModeBar": False}
show = lambda c, f: c.plotly_chart(f, use_container_width=True, config=cfg, theme=None)

# Row 1
c1, c2, c3 = st.columns([1, 1.6, 1.8])
pie = d["Churn"].value_counts().reindex(["No", "Yes"]).fillna(0)
fig = go.Figure(go.Pie(labels=["No", "Yes"], values=pie.values, marker=dict(colors=["#118dff", "#12239e"]),
                       texttemplate="%{percent:.2%}", textposition="outside", sort=False, direction="clockwise",
                       rotation=0, textfont=dict(color="#4a4650", size=15), domain=dict(x=[0, 0.72])))
fig = style(fig, "Total Customers by Churn", 300)
fig.update_layout(showlegend=True, legend=dict(x=0.78, y=0.55, font=dict(color=INK, size=15)),
                  margin=dict(l=20, r=10, t=55, b=20))
show(c1, fig)
show(c2, hbar("PaymentMethod", "Churn Rate by PaymentMethod"))
show(c3, hbar("InternetService", "Churn Rate by InternetService"))

# Row 2
c1, c2, c3, c4 = st.columns([1.8, 1, 1, 1])
show(c1, vbar("Contract", "Churn Rate by Contract", ["Month-to-month", "One year", "Two year"]))
show(c2, vbar("gender", "Churn Rate by gender", ["Female", "Male"], width=0.6))
show(c3, vbar("Partner", "Churn Rate by Partner", ["No", "Yes"], width=0.6))
show(c4, vbar("Dependents", "Churn Rate by Dependents", ["No", "Yes"], width=0.6))

# Row 3
c1, c2, c3 = st.columns([1.8, 2, 1.1])
tx, ty = rate("TenureGroup", ["0-12 Months", "13-24 Months", "25-48 Months", "49+ Months"])
fig = go.Figure(go.Scatter(x=tx, y=ty, mode="lines+markers+text", fill="tozeroy",
                           line=dict(color=BAR, width=3), marker=dict(size=9, color=BAR),
                           fillcolor="rgba(91,59,145,0.4)", text=[f"{v:.2f}%" for v in ty],
                           textposition="top right", textfont=dict(color="#4a4650", size=13), cliponaxis=False))
fig.update_yaxes(visible=False, range=[0, max(ty + [1]) * 1.3])
show(c1, style(fig, "Churn Rate by Tenure Group", 250))

clv = d.groupby("Contract")["TotalCharges"].mean().reindex(["Two year", "One year", "Month-to-month"]).dropna()
show(c2, hbar(None, "Average Customer Lifetime Value by Contract", 250,
              fmt=lambda v: f"{v/1000:.1f}K", data=(clv.index.tolist(), clv.round(0).tolist())))
show(c3, vbar("TechSupport", "Churn Rate by TechSupport", ["No", "Yes", "No internet service"], width=0.6))

st.markdown(f'<div class="foot">Data: Telco Customer Churn · <a href="{REPO_URL}" target="_blank">GitHub repository</a></div>',
            unsafe_allow_html=True)
