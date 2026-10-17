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
div[data-baseweb="select"] > div {{ background:#ffffff !important; border:1px solid #c9c3d6 !important; }}
div[data-baseweb="select"] * {{ color:{INK} !important; }}
div[data-baseweb="popover"], div[data-baseweb="popover"] ul, ul[role="listbox"] {{ background:#ffffff !important; }}
ul[role="listbox"] li {{ background:#ffffff !important; color:{INK} !important; }}
ul[role="listbox"] li:hover, ul[role="listbox"] li[aria-selected="true"] {{ background:#ece6f6 !important; }}
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


# ---------- Chart helpers ----------
def rate(col, order=None):
    r = (d.groupby(col, observed=True)["ChurnFlag"].mean() * 100).round(2).reset_index(name="Rate")
    if order:
        r[col] = pd.Categorical(r[col], order, ordered=True)
        r = r.sort_values(col)
    else:
        r = r.sort_values("Rate", ascending=False)
    return r


def style(fig, title, h=300):
    fig.update_layout(template="plotly_white", title=dict(text=title, font=dict(color=INK, size=17)), height=h,
                      paper_bgcolor="white", plot_bgcolor="white", font=dict(color=INK, size=13),
                      margin=dict(l=10, r=60, t=50, b=10), showlegend=False)
    fig.update_xaxes(showgrid=False, color=INK, title=None, tickfont=dict(color=INK, size=13), automargin=True)
    fig.update_yaxes(showgrid=False, color=INK, title=None, tickfont=dict(color=INK, size=13), automargin=True)
    return fig


def vbar(col, title, order=None, h=280):
    r = rate(col, order)
    fig = px.bar(r, x=col, y="Rate", text=r["Rate"].map(lambda v: f"{v:.2f}%"))
    fig.update_traces(marker_color=BAR, textposition="outside", textfont_color=INK, cliponaxis=False)
    fig.update_yaxes(visible=False)
    return style(fig, title, h)


def hbar(col, title, h=300):
    r = rate(col).sort_values("Rate")
    fig = px.bar(r, x="Rate", y=col, orientation="h", text=r["Rate"].map(lambda v: f"{v:.2f}%"))
    fig.update_traces(marker_color=BAR, textposition="outside", textfont_color=INK, cliponaxis=False)
    fig.update_xaxes(visible=False)
    return style(fig, title, h)


cfg = {"displayModeBar": False}

# Row 1
c1, c2, c3 = st.columns([1, 1.3, 1.3])
pie = d["Churn"].value_counts().reindex(["No", "Yes"]).fillna(0)
fig = go.Figure(go.Pie(labels=pie.index, values=pie.values, marker_colors=["#118dff", "#12239e"],
                       texttemplate="%{percent:.2%}", textposition="outside", sort=False,
                       textfont_color=INK))
fig = style(fig, "Total Customers by Churn")
fig.update_layout(showlegend=True, legend=dict(font=dict(color=INK)))
c1.plotly_chart(fig, use_container_width=True, config=cfg, theme=None)
c2.plotly_chart(hbar("PaymentMethod", "Churn Rate by PaymentMethod"), use_container_width=True, config=cfg, theme=None)
c3.plotly_chart(hbar("InternetService", "Churn Rate by InternetService"), use_container_width=True, config=cfg, theme=None)

# Row 2
c1, c2, c3, c4 = st.columns([1.8, 1, 1, 1])
c1.plotly_chart(vbar("Contract", "Churn Rate by Contract", ["Month-to-month", "One year", "Two year"]),
                use_container_width=True, config=cfg, theme=None)
c2.plotly_chart(vbar("gender", "Churn Rate by gender", ["Female", "Male"]), use_container_width=True, config=cfg, theme=None)
c3.plotly_chart(vbar("Partner", "Churn Rate by Partner", ["No", "Yes"]), use_container_width=True, config=cfg, theme=None)
c4.plotly_chart(vbar("Dependents", "Churn Rate by Dependents", ["No", "Yes"]), use_container_width=True, config=cfg, theme=None)

# Row 3
c1, c2, c3 = st.columns([1.3, 1.3, 1])
t = rate("TenureGroup", ["0-12 Months", "13-24 Months", "25-48 Months", "49+ Months"])
fig = go.Figure(go.Scatter(x=t["TenureGroup"].astype(str), y=t["Rate"], mode="lines+markers+text",
                           fill="tozeroy", line=dict(color=BAR, width=3), fillcolor="rgba(91,59,145,0.35)",
                           text=t["Rate"].map(lambda v: f"{v:.2f}%"), textposition="top right",
                           textfont=dict(color=INK)))
fig.update_yaxes(visible=False, range=[0, t["Rate"].max() * 1.3])
c1.plotly_chart(style(fig, "Churn Rate by Tenure Group"), use_container_width=True, config=cfg, theme=None)

clv = d.groupby("Contract")["TotalCharges"].mean().sort_values().reset_index()
fig = px.bar(clv, x="TotalCharges", y="Contract", orientation="h",
             text=clv["TotalCharges"].map(lambda v: f"{v/1000:.1f}K"))
fig.update_traces(marker_color=BAR, textposition="outside", textfont_color=INK, cliponaxis=False)
fig.update_xaxes(visible=False)
c2.plotly_chart(style(fig, "Average Customer Lifetime Value by Contract"), use_container_width=True, config=cfg, theme=None)
c3.plotly_chart(vbar("TechSupport", "Churn Rate by TechSupport", ["No", "Yes", "No internet service"], 300),
                use_container_width=True, config=cfg, theme=None)

st.markdown(f'<div class="foot">Data: Telco Customer Churn · <a href="{REPO_URL}" target="_blank">GitHub repository</a></div>',
            unsafe_allow_html=True)
