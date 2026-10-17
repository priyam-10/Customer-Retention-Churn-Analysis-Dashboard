"""
Customer Retention & Churn Analysis Dashboard  (Streamlit version)
Replica of the Power BI dashboard, built on the Telco Customer Churn dataset.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------
GITHUB_URL = "https://github.com/priyam-10/Customer-Retention-Churn-Analysis-Dashboard"
RAW_CSV_URL = (
    "https://raw.githubusercontent.com/priyam-10/Customer-Retention-Churn-Analysis-Dashboard/"
    "main/FUTURE_DS_02/Dataset/WA_Fn-UseC_-Telco-Customer-Churn.csv"
)
LOCAL_CSV_CANDIDATES = [
    "FUTURE_DS_02/Dataset/WA_Fn-UseC_-Telco-Customer-Churn.csv",
    "Dataset/WA_Fn-UseC_-Telco-Customer-Churn.csv",
    "WA_Fn-UseC_-Telco-Customer-Churn.csv",
    "data.csv",
]

# Colours (text/background pairs chosen for strong contrast)
PURPLE_DARK = "#3B2667"   # header bar
PURPLE_BAR = "#5B3C91"    # bars / lines
BG_TOP, BG_BOTTOM = "#170D2E", "#2A1857"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#1F1535"     # text on white cards
TEXT_LIGHT = "#FFFFFF"    # text on dark purple
BLUE_NO, BLUE_YES = "#118DFF", "#12239E"

st.set_page_config(
    page_title="Customer Retention & Churn Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# STYLES
# --------------------------------------------------------------------------
st.markdown(
    f"""
<style>
/* ---------- page ---------- */
.stApp {{ background: linear-gradient(135deg, {BG_TOP} 0%, {BG_BOTTOM} 100%); }}
header[data-testid="stHeader"], #MainMenu, footer {{ visibility: hidden; height: 0; }}
.block-container {{ padding: 1rem 1.5rem 2rem 1.5rem; max-width: 1700px; }}
div[data-testid="stHorizontalBlock"] {{ gap: 0.9rem; }}
div[data-testid="stVerticalBlock"] {{ gap: 0.9rem; }}

/* ---------- header ---------- */
.hdr {{
  display:flex; align-items:center; gap:22px; background:{PURPLE_DARK};
  padding:14px 22px; border-radius:6px; flex-wrap:wrap;
}}
.hdr .logo {{
  background:#fff; border-radius:18px; width:84px; height:84px; display:flex;
  align-items:center; justify-content:center; font-size:42px; flex:0 0 auto;
}}
.hdr .ttl {{ flex:1 1 420px; }}
.hdr h1 {{ color:{TEXT_LIGHT}; font-size:2.35rem; font-weight:800; margin:0; padding:0; line-height:1.15; }}
.hdr p  {{ color:{TEXT_LIGHT}; font-size:1.1rem; font-weight:600; margin:6px 0 0 0; }}
.hdr .links {{ display:flex; gap:12px; flex-wrap:wrap; }}
.hdr a.btn {{
  text-decoration:none !important; font-weight:700; font-size:1.05rem; padding:10px 20px;
  border-radius:10px; border:3px solid #000; background:#fff; color:{TEXT_DARK} !important;
  white-space:nowrap;
}}
.hdr a.btn:hover {{ background:#EDE7FA; }}
.hdr a.btn.gh {{ background:#111; color:#fff !important; border-color:#fff; }}
.hdr a.btn.gh:hover {{ background:#333; }}

/* ---------- white cards ---------- */
[class*="st-key-card"] {{
  background:{CARD_BG}; border-radius:16px; padding:12px 16px 8px 16px;
  box-shadow:0 2px 8px rgba(0,0,0,.35); border:1px solid #D9D2EA;
}}
[class*="st-key-card"] * {{ color:{TEXT_DARK}; }}
.card-title {{ font-size:1.12rem; font-weight:700; letter-spacing:.2px; margin:0 0 2px 2px; color:{TEXT_DARK}; }}

/* ---------- KPI cards ---------- */
.kpi {{
  background:{CARD_BG}; border-radius:16px; padding:14px 18px; display:flex; align-items:center;
  justify-content:space-between; box-shadow:0 2px 8px rgba(0,0,0,.35); border:1px solid #D9D2EA;
  min-height:110px;
}}
.kpi .icon {{ font-size:3rem; line-height:1; }}
.kpi .body {{ text-align:right; }}
.kpi .lbl {{ font-size:1.1rem; color:{TEXT_DARK}; font-weight:500; }}
.kpi .val {{ font-size:2.7rem; color:{TEXT_DARK}; font-weight:800; line-height:1.1; }}

/* ---------- filters ---------- */
.st-key-card_filters {{ min-height: 1080px; }}
.st-key-card_filters label p {{ font-weight:700; font-size:1rem; color:{TEXT_DARK} !important; }}
.st-key-card_filters div[data-baseweb="select"] > div {{
  background:#fff; border:1px solid #C9BFE0; color:{TEXT_DARK};
}}
.st-key-card_filters div[data-baseweb="select"] * {{ color:{TEXT_DARK} !important; }}

/* ---------- misc text on dark background ---------- */
.on-dark, .on-dark * {{ color:{TEXT_LIGHT} !important; }}
.footer {{ text-align:center; padding:6px 0 0 0; }}
.footer a {{ color:#FFD166 !important; font-weight:700; }}
.insight-text {{ font-size:1.02rem; line-height:1.55; }}
.insight-text li {{ margin-bottom:6px; }}
.rec-num {{ font-weight:800; color:{PURPLE_BAR}; }}
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# DATA
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading dataset…")
def load_data() -> pd.DataFrame:
    df = None
    for p in LOCAL_CSV_CANDIDATES:
        if Path(p).exists():
            df = pd.read_csv(p)
            break
    if df is None:
        df = pd.read_csv(RAW_CSV_URL)

    # same cleaning as Power Query: blank TotalCharges rows are removed (11 rows)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).copy()

    df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})
    df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)
    df["TenureGroup"] = pd.cut(
        df["tenure"],
        bins=[-1, 12, 24, 48, 10_000],
        labels=["0-12 Months", "13-24 Months", "25-48 Months", "49+ Months"],
    )
    return df


def fmt_k(x: float, prefix: str = "") -> str:
    if abs(x) >= 1000:
        return f"{prefix}{x / 1000:.2f}K"
    return f"{prefix}{x:,.0f}"


def title(text: str) -> None:
    st.markdown(f'<div class="card-title">{text}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------
# CHART HELPERS
# --------------------------------------------------------------------------
def base_layout(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_DARK, size=13, family="Segoe UI, Arial, sans-serif"),
        showlegend=False,
    )
    return fig


def churn_rate(df: pd.DataFrame, col: str, order=None) -> pd.Series:
    s = df.groupby(col, observed=True)["ChurnFlag"].mean() * 100
    if order is not None:
        s = s.reindex([o for o in order if o in s.index])
    return s


def hbar(series: pd.Series, height: int, fmt="{:.2f}%", sort=True) -> go.Figure:
    if sort:
        series = series.sort_values(ascending=False)
    fig = go.Figure(
        go.Bar(
            x=series.values,
            y=series.index.astype(str),
            orientation="h",
            marker_color=PURPLE_BAR,
            text=[fmt.format(v) for v in series.values],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color=TEXT_DARK, size=13),
            hovertemplate="%{y}: %{text}<extra></extra>",
        )
    )
    base_layout(fig, height)
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=TEXT_DARK, size=13))
    fig.update_xaxes(visible=False, range=[0, max(series.max(), 1) * 1.28])
    fig.update_layout(bargap=0.22)
    return fig


def vbar(series: pd.Series, height: int) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=series.index.astype(str),
            y=series.values,
            marker_color=PURPLE_BAR,
            text=[f"{v:.2f}%" for v in series.values],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color=TEXT_DARK, size=13),
            hovertemplate="%{x}: %{text}<extra></extra>",
        )
    )
    base_layout(fig, height)
    fig.update_xaxes(showgrid=False, tickfont=dict(color=TEXT_DARK, size=13))
    fig.update_yaxes(visible=False, range=[0, max(series.max(), 1) * 1.25])
    fig.update_layout(bargap=0.35)
    return fig


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def empty_note() -> None:
    st.info("No customers match the selected filters.")


# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
def header(page: str) -> None:
    if page == "dashboard":
        sub = "Customer Segmentation, Retention Trends &amp; Churn Driver Analysis"
        main_btn = '<a class="btn" href="?page=insights" target="_self">View Detailed Insights →</a>'
        head = "Customer Retention &amp; Churn Analysis Dashboard"
    else:
        sub = "Key Findings, Retention Drivers &amp; Business Recommendations"
        main_btn = '<a class="btn" href="?page=dashboard" target="_self">← Back to Dashboard</a>'
        head = "Insights &amp; Recommendations"
    st.markdown(
        f"""
<div class="hdr">
  <div class="logo">💜👥</div>
  <div class="ttl"><h1>{head}</h1><p>{sub}</p></div>
  <div class="links">
    {main_btn}
    <a class="btn gh" href="{GITHUB_URL}" target="_blank">⭐ GitHub Repo</a>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        f"""
<div class="footer on-dark">
  Built with Streamlit &amp; Plotly · Data: Telco Customer Churn ·
  <a href="{GITHUB_URL}" target="_blank">View source on GitHub</a>
</div>
""",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# PAGE 1 – DASHBOARD
# --------------------------------------------------------------------------
def dashboard_page(df: pd.DataFrame) -> None:
    header("dashboard")

    left, right = st.columns([1.05, 6], gap="small")

    # ---------------- filters ----------------
    with left:
        with st.container(key="card_filters"):
            filter_defs = [
                ("Contract Type", "Contract"),
                ("Internet Services", "InternetService"),
                ("Payment Method", "PaymentMethod"),
                ("Gender", "gender"),
                ("SeniorCitizen", "SeniorCitizen"),
                ("Phone Service", "PhoneService"),
                ("Partner", "Partner"),
                ("Dependents", "Dependents"),
            ]
            selections = {}
            for label, col in filter_defs:
                opts = ["All"] + sorted(df[col].dropna().unique().tolist())
                selections[col] = st.selectbox(label, opts, key=f"f_{col}")

    f = df.copy()
    for col, val in selections.items():
        if val != "All":
            f = f[f[col] == val]

    with right:
        # ---------------- KPI row ----------------
        total = len(f)
        churned = int(f["ChurnFlag"].sum())
        retained = total - churned
        avg_tenure = f["tenure"].mean() if total else 0
        avg_total = f["TotalCharges"].mean() if total else 0

        kpis = [
            ("👥", "Total Customers", fmt_k(total)),
            ("🚫", "Churned Customers", fmt_k(churned)),
            ("📈", "Retained Customers", fmt_k(retained)),
            ("⏱️", "Avg Tenure", f"{avg_tenure:.2f}"),
            ("💰", "Avg Total Charges", fmt_k(avg_total, "$")),
        ]
        for col, (icon, lbl, val) in zip(st.columns(5), kpis):
            col.markdown(
                f'<div class="kpi"><div class="icon">{icon}</div>'
                f'<div class="body"><div class="lbl">{lbl}</div><div class="val">{val}</div></div></div>',
                unsafe_allow_html=True,
            )

        if total == 0:
            empty_note()
            return

        # ---------------- row A ----------------
        c1, c2, c3 = st.columns([1.45, 2.4, 2.6])

        with c1:
            with st.container(key="card_pie"):
                title("Total Customers by Churn")
                pie = go.Figure(
                    go.Pie(
                        labels=["No", "Yes"],
                        values=[retained, churned],
                        marker=dict(colors=[BLUE_NO, BLUE_YES], line=dict(color="#fff", width=1)),
                        texttemplate="%{percent:.2%}",
                        textposition="outside",
                        textfont=dict(color=TEXT_DARK, size=14),
                        sort=False,
                        direction="clockwise",
                        rotation=0,
                        hovertemplate="Churn = %{label}: %{value:,}<extra></extra>",
                    )
                )
                base_layout(pie, 330)
                pie.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center",
                                font=dict(color=TEXT_DARK, size=13)),
                    margin=dict(l=30, r=30, t=20, b=20),
                )
                show(pie)

        with c2:
            with st.container(key="card_pay"):
                title("Churn Rate by PaymentMethod")
                show(hbar(churn_rate(f, "PaymentMethod"), 330))

        with c3:
            with st.container(key="card_net"):
                title("Churn Rate by InternetService")
                show(hbar(churn_rate(f, "InternetService"), 330))

        # ---------------- row B ----------------
        b1, b2, b3, b4 = st.columns([3, 1.6, 1.6, 1.6])
        with b1:
            with st.container(key="card_contract"):
                title("Churn Rate by Contract")
                show(vbar(churn_rate(f, "Contract", ["Month-to-month", "One year", "Two year"]), 270))
        with b2:
            with st.container(key="card_gender"):
                title("Churn Rate by gender")
                show(vbar(churn_rate(f, "gender", ["Female", "Male"]), 270))
        with b3:
            with st.container(key="card_partner"):
                title("Churn Rate by Partner")
                show(vbar(churn_rate(f, "Partner", ["No", "Yes"]), 270))
        with b4:
            with st.container(key="card_dep"):
                title("Churn Rate by Dependents")
                show(vbar(churn_rate(f, "Dependents", ["No", "Yes"]), 270))

        # ---------------- row C ----------------
        d1, d2, d3 = st.columns([3, 3.2, 1.9])

        with d1:
            with st.container(key="card_tenure"):
                title("Churn Rate by Tenure Group")
                tg = churn_rate(
                    f, "TenureGroup",
                    ["0-12 Months", "13-24 Months", "25-48 Months", "49+ Months"],
                )
                fig = go.Figure(
                    go.Scatter(
                        x=tg.index.astype(str),
                        y=tg.values,
                        mode="lines+markers+text",
                        fill="tozeroy",
                        fillcolor="rgba(91,60,145,0.40)",
                        line=dict(color=PURPLE_BAR, width=3),
                        marker=dict(color=PURPLE_BAR, size=9),
                        text=[f"{v:.2f}%" for v in tg.values],
                        textposition="top center",
                        textfont=dict(color=TEXT_DARK, size=13),
                        cliponaxis=False,
                        hovertemplate="%{x}: %{text}<extra></extra>",
                    )
                )
                base_layout(fig, 290)
                fig.update_xaxes(showgrid=False, tickfont=dict(color=TEXT_DARK, size=13))
                fig.update_yaxes(visible=False, range=[0, max(tg.max(), 1) * 1.35])
                show(fig)

        with d2:
            with st.container(key="card_clv"):
                title("Average Customer Lifetime Value by Contract")
                clv = f.groupby("Contract")["TotalCharges"].mean()
                clv = clv.reindex([c for c in ["Two year", "One year", "Month-to-month"] if c in clv.index])
                fig = go.Figure(
                    go.Bar(
                        x=clv.values,
                        y=clv.index,
                        orientation="h",
                        marker_color=PURPLE_BAR,
                        text=[f"{v / 1000:.1f}K" for v in clv.values],
                        textposition="outside",
                        cliponaxis=False,
                        textfont=dict(color=TEXT_DARK, size=13),
                        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
                    )
                )
                base_layout(fig, 290)
                fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=TEXT_DARK, size=13))
                fig.update_xaxes(visible=False, range=[0, max(clv.max(), 1) * 1.2])
                fig.update_layout(bargap=0.25)
                show(fig)

        with d3:
            with st.container(key="card_tech"):
                title("Churn Rate by TechSupport")
                ts = churn_rate(f, "TechSupport", ["No", "Yes", "No internet service"])
                ts.index = [("No inte…" if i == "No internet service" else i) for i in ts.index]
                show(vbar(ts, 290))

    footer()


# --------------------------------------------------------------------------
# PAGE 2 – INSIGHTS
# --------------------------------------------------------------------------
def insights_page(df: pd.DataFrame) -> None:
    header("insights")

    total, churned = len(df), int(df["ChurnFlag"].sum())
    rate = churned / total * 100
    r = lambda col: df.groupby(col, observed=True)["ChurnFlag"].mean() * 100  # noqa: E731
    contract, internet, pay = r("Contract"), r("InternetService"), r("PaymentMethod")
    tech, tenure = r("TechSupport"), r("TenureGroup")
    clv = df.groupby("Contract")["TotalCharges"].mean()

    cols = st.columns(4)
    kp = [
        ("Churn Rate", f"{rate:.2f}%"),
        ("Retention Rate", f"{100 - rate:.2f}%"),
        ("Avg Tenure (months)", f"{df['tenure'].mean():.2f}"),
        ("Avg Lifetime Value", fmt_k(df["TotalCharges"].mean(), "$")),
    ]
    for c, (lbl, val) in zip(cols, kp):
        c.markdown(
            f'<div class="kpi"><div class="body" style="text-align:left"><div class="lbl">{lbl}</div>'
            f'<div class="val">{val}</div></div></div>',
            unsafe_allow_html=True,
        )

    a, b, c = st.columns(3)
    with a:
        with st.container(key="card_i1"):
            title("📉 Churn Patterns")
            st.markdown(
                f"""<div class="insight-text"><ul>
<li>Month-to-month contracts churn the most (<b>{contract['Month-to-month']:.2f}%</b>) vs two-year (<b>{contract['Two year']:.2f}%</b>).</li>
<li>Customers in their first 12 months churn at <b>{tenure['0-12 Months']:.2f}%</b>; 49+ months only <b>{tenure['49+ Months']:.2f}%</b>.</li>
<li>Fiber optic churn (<b>{internet['Fiber optic']:.2f}%</b>) is more than double DSL (<b>{internet['DSL']:.2f}%</b>).</li>
<li>Electronic check users churn at <b>{pay['Electronic check']:.2f}%</b>, the highest of all payment methods.</li>
</ul></div>""",
                unsafe_allow_html=True,
            )
    with b:
        with st.container(key="card_i2"):
            title("💰 Customer Lifetime Value")
            st.markdown(
                f"""<div class="insight-text"><ul>
<li>Two-year contract customers generate the highest value: <b>${clv['Two year']:,.0f}</b> on average.</li>
<li>One-year customers average <b>${clv['One year']:,.0f}</b>; month-to-month only <b>${clv['Month-to-month']:,.0f}</b>.</li>
<li>Customer value rises with tenure – long-term customers contribute far more revenue.</li>
</ul></div>""",
                unsafe_allow_html=True,
            )
    with c:
        with st.container(key="card_i3"):
            title("📈 Retention Drivers")
            st.markdown(
                f"""<div class="insight-text"><ul>
<li>Contract type is the strongest retention driver.</li>
<li>Tech support matters: churn is <b>{tech['No']:.2f}%</b> without it vs <b>{tech['Yes']:.2f}%</b> with it.</li>
<li>Long-term relationships steadily reduce churn risk.</li>
</ul></div>""",
                unsafe_allow_html=True,
            )

    with st.container(key="card_recs"):
        title("💡 Business Recommendations")
        recs = [
            ("Promote Long-Term Contracts", "Encourage customers to move from month-to-month plans to annual or two-year contracts."),
            ("Improve Customer Onboarding", "Strengthen engagement during the first 12 months to reduce early-stage churn."),
            ("Investigate Fiber Optic Churn", "Analyse service quality, pricing and satisfaction among Fiber Optic users."),
            ("Encourage Automatic Payments", "Promote automatic payment methods to improve customer retention."),
            ("Bundle Tech Support Services", "Offer bundled support plans to increase satisfaction and reduce churn."),
        ]
        rc = st.columns(5)
        for i, (col, (h, t)) in enumerate(zip(rc, recs), start=1):
            col.markdown(
                f'<div class="insight-text"><span class="rec-num">{i}. {h}</span><br>{t}</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
<div class="on-dark" style="margin-top:6px">
  <b>Project:</b> Future Interns – Data Science &amp; Analytics Internship, Task 2 ·
  <b>Author:</b> Priyam Singh ·
  <a href="{GITHUB_URL}" target="_blank" style="color:#FFD166 !important;font-weight:700">GitHub repository</a>
</div>
""",
        unsafe_allow_html=True,
    )
    footer()


# --------------------------------------------------------------------------
# ROUTER
# --------------------------------------------------------------------------
data = load_data()
page = st.query_params.get("page", "dashboard")
if page == "insights":
    insights_page(data)
else:
    dashboard_page(data)
