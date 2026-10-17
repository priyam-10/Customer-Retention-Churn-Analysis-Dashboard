import io
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
import requests

REPO_URL = "https://github.com/priyam-10/Customer-Retention-Churn-Analysis-Dashboard"
DATA_URL = "https://raw.githubusercontent.com/priyam-10/Customer-Retention-Churn-Analysis-Dashboard/main/FUTURE_DS_02/Dataset/WA_Fn-UseC_-Telco-Customer-Churn.csv"

st.set_page_config(page_title="Customer Retention & Churn Analytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top:1.25rem; padding-bottom:2rem}
div[data-testid="stMetric"] {border:1px solid rgba(128,128,128,.25); padding:14px; border-radius:12px}
</style>
""", unsafe_allow_html=True)

st.title("📊 Customer Retention & Churn Analysis")
st.caption("Interactive customer analytics · Churn drivers · Retention opportunities")
st.markdown(f"**Project repository:** [{REPO_URL}]({REPO_URL})")
st.markdown("This Streamlit edition recreates the main analysis areas described in the original Power BI project.")

@st.cache_data(ttl=3600, show_spinner=False)
def load_repo_data():
    r = requests.get(DATA_URL, timeout=30)
    r.raise_for_status()
    return pd.read_csv(io.BytesIO(r.content))

def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    # Standard Telco dataset numeric fields are sometimes imported as strings.
    for col in ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Churn" in df.columns:
        df["Churn"] = df["Churn"].astype(str).str.strip()
    return df

def churn_rate(frame, group_col):
    return (frame.groupby(group_col, dropna=False)["Churn"]
            .apply(lambda s: (s == "Yes").mean() * 100)
            .rename("Churn rate (%)").reset_index()
            .sort_values("Churn rate (%)", ascending=False))

def make_report(frame):
    n = len(frame)
    churned = int((frame["Churn"] == "Yes").sum()) if "Churn" in frame else 0
    retained = int((frame["Churn"] == "No").sum()) if "Churn" in frame else 0
    rate = churned / n * 100 if n else 0
    lines = [
        "CUSTOMER RETENTION & CHURN ANALYSIS REPORT",
        "=" * 44,
        f"Generated: {date.today().isoformat()}",
        f"Customers in current filter: {n:,}",
        f"Churned customers: {churned:,}",
        f"Retained customers: {retained:,}",
        f"Churn rate: {rate:.2f}%",
        f"Retention rate: {100-rate:.2f}%",
    ]
    if "tenure" in frame:
        lines.append(f"Average tenure: {frame['tenure'].mean():.2f} months")
    if "MonthlyCharges" in frame:
        lines.append(f"Average monthly charges: {frame['MonthlyCharges'].mean():.2f}")
    if "TotalCharges" in frame:
        lines.append(f"Total charges across selected customers: {frame['TotalCharges'].sum():,.2f}")
    lines += ["", "SEGMENT FINDINGS"]
    for col in ["Contract", "InternetService", "PaymentMethod", "TechSupport"]:
        if col in frame and "Churn" in frame and frame[col].nunique(dropna=True) > 0:
            rates = churn_rate(frame, col)
            if not rates.empty:
                row = rates.iloc[0]
                lines.append(f"Highest churn-rate {col} segment: {row[col]} ({row['Churn rate (%)']:.2f}%)")
    lines += [
        "", "INTERPRETATION",
        "These findings describe the selected historical data; they do not establish causation or predict future churn.",
        "Use the segment findings to prioritize further investigation and retention experiments.",
        "", f"Source repository: {REPO_URL}",
    ]
    return "\n".join(lines)

with st.sidebar:
    st.header("Data")
    st.link_button("Open GitHub repository", REPO_URL, use_container_width=True)
    uploaded = st.file_uploader("Or upload a CSV dataset", type=["csv"])
    st.divider()
    st.caption("Filters apply to KPIs, charts, and the downloadable report.")

try:
    if uploaded:
        data = pd.read_csv(uploaded)
        source_label = uploaded.name
    else:
        with st.spinner("Loading the dataset from your GitHub repository…"):
            data = load_repo_data()
        source_label = "GitHub repository dataset"
except Exception as e:
    st.error("The dataset could not be loaded automatically. Check that the repository is public and the CSV path is correct, or upload the CSV using the sidebar.")
    with st.expander("Technical details"):
        st.code(str(e))
    st.stop()

df = normalize_columns(data)
required = {"Churn"}
if not required.issubset(df.columns):
    st.error("This dashboard expects the Telco Customer Churn dataset with a 'Churn' column. Please upload the matching dataset.")
    st.stop()

# Keep blank TotalCharges values as missing, not zero; normalize common text categories.
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].replace({"": None, "nan": None, "NaN": None})

with st.sidebar:
    st.header("Dashboard filters")
    filtered = df.copy()
    if "Churn" in filtered:
        vals = sorted(filtered["Churn"].dropna().unique().tolist())
        selected = st.multiselect("Churn status", vals, default=vals)
        if selected:
            filtered = filtered[filtered["Churn"].isin(selected)]
    filter_cols = [
        ("Contract", "Contract type"),
        ("InternetService", "Internet service"),
        ("PaymentMethod", "Payment method"),
        ("TechSupport", "Tech support"),
        ("gender", "Gender"),
    ]
    for col, label in filter_cols:
        if col in filtered:
            vals = sorted(filtered[col].dropna().astype(str).unique().tolist())
            selected = st.multiselect(label, vals, key=f"filter_{col}")
            if selected:
                filtered = filtered[filtered[col].astype(str).isin(selected)]

if filtered.empty:
    st.warning("No customers match these filters. Change the filters in the sidebar.")
    st.stop()

n = len(filtered)
churned = int((filtered["Churn"] == "Yes").sum())
retained = int((filtered["Churn"] == "No").sum())
rate = churned / n * 100 if n else 0

st.caption(f"**Source:** {source_label} · **Rows in view:** {n:,} · **Dataset rows:** {len(df):,}")
st.subheader("Executive overview")
k = st.columns(4)
k[0].metric("Total customers", f"{n:,}")
k[1].metric("Churned customers", f"{churned:,}")
k[2].metric("Churn rate", f"{rate:.2f}%")
k[3].metric("Retention rate", f"{100-rate:.2f}%")
k2 = st.columns(3)
if "tenure" in filtered:
    k2[0].metric("Average tenure", f"{filtered['tenure'].mean():.1f} months")
if "MonthlyCharges" in filtered:
    k2[1].metric("Average monthly charges", f"{filtered['MonthlyCharges'].mean():,.2f}")
if "TotalCharges" in filtered:
    k2[2].metric("Total charges", f"{filtered['TotalCharges'].sum():,.2f}")

overview, drivers, value, explorer, report_tab = st.tabs([
    "📌 Overview", "🔎 Churn drivers", "💰 Customer value", "🧾 Data explorer", "📝 Report"
])

with overview:
    left, right = st.columns(2)
    counts = filtered["Churn"].value_counts().rename_axis("Churn status").reset_index(name="Customers")
    left.plotly_chart(px.pie(counts, names="Churn status", values="Customers",
                             title="Customer churn distribution", hole=.45), use_container_width=True)
    if "tenure" in filtered:
        tenure = filtered.dropna(subset=["tenure"]).copy()
        tenure["Tenure group"] = pd.cut(tenure["tenure"], bins=[-1, 12, 24, 48, 72],
                                         labels=["0–12 months", "13–24 months", "25–48 months", "49–72 months"])
        grp = tenure.groupby(["Tenure group", "Churn"], observed=False).size().reset_index(name="Customers")
        right.plotly_chart(px.bar(grp, x="Tenure group", y="Customers", color="Churn",
                                  barmode="group", title="Customer lifecycle by tenure"), use_container_width=True)
    else:
        right.info("A tenure column is required for lifecycle analysis.")

with drivers:
    chart_cols = st.columns(2)
    for idx, (col, title) in enumerate([
        ("Contract", "Churn rate by contract type"),
        ("InternetService", "Churn rate by internet service"),
        ("PaymentMethod", "Churn rate by payment method"),
        ("TechSupport", "Churn rate by tech support"),
    ]):
        if col in filtered:
            rates = churn_rate(filtered, col)
            chart_cols[idx % 2].plotly_chart(
                px.bar(rates, x=col, y="Churn rate (%)", title=title, text_auto=".1f"),
                use_container_width=True
            )
        else:
            chart_cols[idx % 2].info(f"Column '{col}' is not present in the selected dataset.")
    if "MonthlyCharges" in filtered:
        plot_cols = [c for c in ["MonthlyCharges", "tenure", "Churn"] if c in filtered]
        if len(plot_cols) == 3:
            st.plotly_chart(px.scatter(filtered, x="tenure", y="MonthlyCharges", color="Churn",
                                       title="Monthly charges vs tenure", opacity=.65),
                            use_container_width=True)

with value:
    if "TotalCharges" in filtered and "Churn" in filtered:
        val = filtered.groupby("Churn", as_index=False)["TotalCharges"].mean()
        st.plotly_chart(px.bar(val, x="Churn", y="TotalCharges",
                               title="Average total charges by churn status", text_auto=".2f"),
                        use_container_width=True)
    if "Contract" in filtered and "TotalCharges" in filtered:
        contract_value = filtered.groupby("Contract", as_index=False)["TotalCharges"].mean().sort_values("TotalCharges", ascending=False)
        st.plotly_chart(px.bar(contract_value, x="Contract", y="TotalCharges",
                               title="Average total charges by contract", text_auto=".2f"),
                        use_container_width=True)
    st.caption("Total Charges is shown as an available customer-value proxy; it is not a modeled customer lifetime value unless your source defines it that way.")

with explorer:
    st.write("Inspect the filtered customer records and export them for further analysis.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download filtered customers (CSV)",
                       filtered.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_customer_churn.csv", mime="text/csv")

with report_tab:
    report = make_report(filtered)
    st.text(report)
    st.download_button("⬇️ Download business report (TXT)", report.encode("utf-8"),
                       file_name="customer_retention_churn_report.txt", mime="text/plain")
    st.markdown("### Suggested retention actions")
    st.markdown("""
    - Review the highest-churn contract and payment segments before choosing a campaign.
    - Prioritize onboarding and support for early-tenure customers if the filtered data supports that pattern.
    - Test retention offers on a controlled segment and compare results with a holdout group.
    - Validate any proposed action against customer policy and actual business constraints.
    """)

st.divider()
st.markdown(f"**Source code:** [{REPO_URL}]({REPO_URL}) · Built with Streamlit and Plotly")
