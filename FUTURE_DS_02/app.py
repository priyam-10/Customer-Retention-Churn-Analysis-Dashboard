import io
from datetime import date
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

REPO_URL = "https://github.com/priyam-10/Customer-Retention-Churn-Analysis-Dashboard"
# The earlier starter used this common Telco churn dataset path. If your repo uses another path,
# use the CSV uploader in the sidebar or update DATA_URL below.
DATA_URL = "https://raw.githubusercontent.com/priyam-10/Customer-Retention-Churn-Analysis-Dashboard/main/FUTURE_DS_02/Dataset/WA_Fn-UseC_-Telco-Customer-Churn.csv"

st.set_page_config(page_title="Customer Retention & Churn Analysis Dashboard", page_icon="💜", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { --purple:#39245f; --bar:#5b3b91; --ink:#28252d; }
.stApp { background: linear-gradient(135deg,#180d45 0%,#28105d 55%,#130b39 100%); }
.block-container {padding: 1rem 1.25rem 1.2rem; max-width: 1800px;}
header[data-testid="stHeader"] {background: transparent;}
h1,h2,h3,p,label,span,div { }
.hero {background:#39245f; border:1px solid #7761a3; border-radius:8px; padding:16px 20px; color:white; margin-bottom:8px;}
.hero-title {font-size:30px; font-weight:800; line-height:1.1;}
.hero-sub {font-size:15px; font-weight:600; margin-top:5px;}
.hero a {color:white !important;}
[data-testid="stMetric"] {background:#fff; border:1px solid #d4d0da; border-radius:12px; padding:12px 14px; min-height:100px;}
[data-testid="stMetricLabel"] {color:#27232d; font-size:14px;}
[data-testid="stMetricValue"] {color:#28252d; font-size:29px;}
[data-testid="stVerticalBlockBorderWrapper"] {background:#fff; border-radius:12px; padding:5px;}
section[data-testid="stSidebar"] {background:#f8f7fb;}
section[data-testid="stSidebar"] * {color:#28252d;}
div[data-testid="stPlotlyChart"] {background:#fff; border-radius:10px; padding:4px;}
.stTabs [data-baseweb="tab-list"] {gap:8px;}
.stTabs [data-baseweb="tab"] {background:#f5f2fa; border-radius:8px 8px 0 0; padding:8px 15px;}
a {color:#4d3181;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800, show_spinner=False)
def load_repo_data():
    r = requests.get(DATA_URL, timeout=25)
    r.raise_for_status()
    return pd.read_csv(io.BytesIO(r.content))

def clean_data(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for c in ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in df.select_dtypes(include="object"):
        df[c] = df[c].replace({"": None, "nan": None, "NaN": None})
    if "Churn" in df:
        df["Churn"] = df["Churn"].astype(str).str.strip()
    return df

def pct_by(df, col):
    return (df.groupby(col, dropna=False)["Churn"]
            .apply(lambda s: (s == "Yes").mean() * 100)
            .rename("Churn Rate").reset_index()
            .sort_values("Churn Rate", ascending=False))

def plot_style(fig, title=None, height=250):
    fig.update_layout(
        title=dict(text=title or "", x=0.02, xanchor="left", font=dict(size=17, color="#28252d")),
        height=height, margin=dict(l=10,r=12,t=42,b=12),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial", size=12, color="#77737b"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, linecolor="#eeeeef")
    fig.update_yaxes(showgrid=False, gridcolor="#eeeeef")
    return fig

with st.container():
    st.markdown(f"""
    <div class="hero">
      <div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;">
        <div style="font-size:42px;background:white;border-radius:14px;padding:7px;">💝</div>
        <div style="flex:1;min-width:300px;">
          <div class="hero-title">Customer Retention &amp; Churn Analysis Dashboard</div>
          <div class="hero-sub">Customer Segmentation, Retention Trends &amp; Churn Driver Analysis</div>
        </div>
        <a href="{REPO_URL}" target="_blank" style="text-decoration:none;background:white;color:#17131d !important;border:2px solid #17131d;border-radius:12px;padding:12px 17px;font-weight:700;">View GitHub Repository →</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Dashboard Filters")
    st.markdown(f"[Open project repository ↗]({REPO_URL})")
    uploaded = st.file_uploader("Upload your churn CSV", type=["csv"])
    st.caption("If the repository CSV cannot load, upload the dataset used in Power BI.")
    st.divider()

try:
    if uploaded:
        raw = pd.read_csv(uploaded)
        source = uploaded.name
    else:
        raw = load_repo_data()
        source = "GitHub dataset"
except Exception as e:
    st.warning("Automatic dataset loading did not work. Upload your churn CSV in the sidebar.")
    with st.expander("Technical details"):
        st.code(str(e))
    st.stop()

df = clean_data(raw)
if "Churn" not in df.columns:
    st.error("This dataset needs a 'Churn' column. Please upload the customer churn CSV used in your Power BI dashboard.")
    st.stop()

# Filters matching the screenshot
filter_cols = [
    ("Contract", "Contract Type"),
    ("InternetService", "Internet Services"),
    ("PaymentMethod", "Payment Method"),
    ("gender", "Gender"),
    ("SeniorCitizen", "SeniorCitizen"),
    ("PhoneService", "Phone Service"),
    ("Partner", "Partner"),
    ("Dependents", "Dependents"),
]
with st.sidebar:
    selections = {}
    for col, label in filter_cols:
        if col in df:
            vals = sorted(df[col].dropna().astype(str).unique().tolist())
            selections[col] = st.selectbox(label, ["All"] + vals, index=0)
        else:
            selections[col] = "All"

f = df.copy()
for col, choice in selections.items():
    if col in f and choice != "All":
        f = f[f[col].astype(str) == choice]
if f.empty:
    st.warning("No rows match these filters. Please change one or more filters.")
    st.stop()

n = len(f)
churn_n = int((f["Churn"] == "Yes").sum())
retained_n = int((f["Churn"] == "No").sum())
churn_rate = churn_n / n * 100 if n else 0
avg_tenure = f["tenure"].mean() if "tenure" in f else float("nan")
avg_total = f["TotalCharges"].mean() if "TotalCharges" in f else float("nan")

# KPI row styled to resemble the reference image
k = st.columns(5, gap="small")
k[0].metric("👥  Total Customers", f"{n/1000:.2f}K" if n >= 1000 else f"{n:,}")
k[1].metric("🚫  Churned Customers", f"{churn_n/1000:.2f}K" if churn_n >= 1000 else f"{churn_n:,}")
k[2].metric("🌟  Retained Customers", f"{retained_n/1000:.2f}K" if retained_n >= 1000 else f"{retained_n:,}")
k[3].metric("⏱️  Avg Tenure", f"{avg_tenure:.2f}" if pd.notna(avg_tenure) else "—")
k[4].metric("💰  Avg Total Charges", f"${avg_total/1000:.2f}K" if pd.notna(avg_total) and avg_total >= 1000 else (f"${avg_total:,.2f}" if pd.notna(avg_total) else "—"))

purple = "#5b3b91"
blue = "#168bf5"
darkblue = "#172c9c"
tab1, tab2 = st.tabs(["📊 Dashboard", "🔎 Detailed Insights"])

with tab1:
    top = st.columns([1.05, 1.8, 2.7, 2.7], gap="small")
    # Churn distribution donut/pie
    counts = f["Churn"].value_counts().reindex(["No","Yes"]).dropna().rename_axis("Churn").reset_index(name="Customers")
    fig = px.pie(counts, names="Churn", values="Customers", hole=0,
                 color="Churn", color_discrete_map={"No":blue,"Yes":darkblue})
    fig.update_traces(texttemplate="%{percent:.2%}", textposition="outside", marker=dict(line=dict(color="white", width=1)))
    top[0].plotly_chart(plot_style(fig, "Total Customers by Churn", 285), use_container_width=True)

    if "PaymentMethod" in f:
        p = pct_by(f, "PaymentMethod")
        fig = px.bar(p, x="Churn Rate", y="PaymentMethod", orientation="h", text=p["Churn Rate"].map(lambda x:f"{x:.2f}%"), color_discrete_sequence=[purple])
        fig.update_traces(textposition="outside", cliponaxis=False)
        top[1].plotly_chart(plot_style(fig, "Churn Rate by PaymentMethod", 285), use_container_width=True)
    if "InternetService" in f:
        p = pct_by(f, "InternetService")
        fig = px.bar(p, x="Churn Rate", y="InternetService", orientation="h", text=p["Churn Rate"].map(lambda x:f"{x:.2f}%"), color_discrete_sequence=[purple])
        fig.update_traces(textposition="outside", cliponaxis=False)
        top[2].plotly_chart(plot_style(fig, "Churn Rate by InternetService", 285), use_container_width=True)

    bottom = st.columns([2.2, 1.15, 1.15, 1.15], gap="small")
    if "Contract" in f:
        p = pct_by(f, "Contract").sort_values("Churn Rate")
        fig = px.bar(p, x="Contract", y="Churn Rate", text=p["Churn Rate"].map(lambda x:f"{x:.2f}%"), color_discrete_sequence=[purple])
        fig.update_traces(textposition="outside", cliponaxis=False)
        bottom[0].plotly_chart(plot_style(fig, "Churn Rate by Contract", 220), use_container_width=True)
    for col, title, idx in [("gender","Churn Rate by gender",1),("Partner","Churn Rate by Partner",2),("Dependents","Churn Rate by Dependents",3)]:
        if col in f:
            p = pct_by(f, col).sort_values(col)
            fig = px.bar(p, x=col, y="Churn Rate", text=p["Churn Rate"].map(lambda x:f"{x:.2f}%"), color_discrete_sequence=[purple])
            fig.update_traces(textposition="outside", cliponaxis=False)
            bottom[idx].plotly_chart(plot_style(fig, title, 220), use_container_width=True)

    lower = st.columns([2.2, 2.4, 1.3], gap="small")
    if "tenure" in f:
        t = f.copy()
        t["Tenure Group"] = pd.cut(t["tenure"], bins=[-1,12,24,48,1000],
                                   labels=["0-12 Months","13-24 Months","25-48 Months","49+ Months"])
        p = pct_by(t.dropna(subset=["Tenure Group"]), "Tenure Group")
        order = ["0-12 Months","13-24 Months","25-48 Months","49+ Months"]
        p["Tenure Group"] = pd.Categorical(p["Tenure Group"], categories=order, ordered=True)
        p = p.sort_values("Tenure Group")
        fig = px.area(p, x="Tenure Group", y="Churn Rate", markers=True, color_discrete_sequence=[purple])
        lower[0].plotly_chart(plot_style(fig, "Churn Rate by Tenure Group", 205), use_container_width=True)
    if "Contract" in f and "TotalCharges" in f:
        p = f.groupby("Contract", as_index=False)["TotalCharges"].mean().sort_values("TotalCharges")
        fig = px.bar(p, x="TotalCharges", y="Contract", orientation="h", text=p["TotalCharges"].map(lambda x:f"{x/1000:.1f}K"), color_discrete_sequence=[purple])
        fig.update_traces(textposition="inside")
        lower[1].plotly_chart(plot_style(fig, "Average Customer Lifetime Value by Contract", 205), use_container_width=True)
    if "TechSupport" in f:
        p = pct_by(f, "TechSupport")
        fig = px.bar(p, x="TechSupport", y="Churn Rate", text=p["Churn Rate"].map(lambda x:f"{x:.2f}%"), color_discrete_sequence=[purple])
        fig.update_traces(textposition="outside", cliponaxis=False)
        lower[2].plotly_chart(plot_style(fig, "Churn Rate by TechSupport", 205), use_container_width=True)

with tab2:
    st.subheader("Detailed churn insights")
    a, b = st.columns(2)
    for col, title, slot in [("Contract","Churn by contract",a),("PaymentMethod","Churn by payment method",b),
                             ("InternetService","Churn by internet service",a),("TechSupport","Churn by tech support",b)]:
        if col in f:
            counts = f.groupby([col,"Churn"]).size().reset_index(name="Customers")
            slot.plotly_chart(plot_style(px.bar(counts, x=col, y="Customers", color="Churn", barmode="group",
                                                  color_discrete_map={"No":blue,"Yes":darkblue}), title, 300),
                              use_container_width=True)
    st.subheader("Filtered customer records")
    st.dataframe(f, use_container_width=True, hide_index=True)
    st.download_button("Download filtered data CSV", f.to_csv(index=False).encode("utf-8"),
                       "filtered_churn_customers.csv", "text/csv")
    report = f"""CUSTOMER RETENTION & CHURN REPORT
Generated: {date.today().isoformat()}
Rows in current filter: {n}
Churned customers: {churn_n}
Retained customers: {retained_n}
Churn rate: {churn_rate:.2f}%
Retention rate: {100-churn_rate:.2f}%
Average tenure: {avg_tenure:.2f} months
Average total charges: {avg_total:.2f}

Source repository: {REPO_URL}
"""
    st.download_button("Download report TXT", report, "customer_churn_report.txt", "text/plain")

st.markdown(f"<div style='text-align:center;color:#eee;padding:8px'>Built with Streamlit · <a style='color:white' href='{REPO_URL}'>View GitHub Repository</a></div>", unsafe_allow_html=True)
