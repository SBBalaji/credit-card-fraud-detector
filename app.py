# app.py

import streamlit as st
import pandas as pd

# Safe import for matplotlib
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    st.error("❌ 'matplotlib' is not installed. Add it to requirements.txt or run: pip install matplotlib")
    st.stop()

# Safe import for AgGrid
try:
    from st_aggrid import AgGrid
except ModuleNotFoundError:
    st.error("❌ 'streamlit-aggrid' is not installed. Add it to requirements.txt or run: pip install streamlit-aggrid")
    st.stop()

# ✅ Configure Streamlit page
st.set_page_config(page_title="Credit Card Fraud Detector", layout="wide")

# Title
st.title("💳 Credit Card Fraud Detector")

# Sidebar Menu
with st.sidebar:
    st.title("📚 Menu")
    section = st.radio("Choose a section:", ["Upload Data", "Overview Stats", "Index Viewer", "Visualizations"])

# Helper: Group consecutive indices
def get_contiguous_ranges(indices):
    if not indices:
        return []
    ranges = []
    start = prev = indices[0]
    for i in indices[1:]:
        if i == prev + 1:
            prev = i
        else:
            ranges.append((start, prev))
            start = prev = i
    ranges.append((start, prev))
    return ranges

# Upload file
uploaded_file = st.file_uploader("📂 Upload your `creditcard.csv` file", type=["csv"])

if uploaded_file is not None:
    try:
        card = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")
        st.stop()

    if 'Time' not in card.columns or 'Class' not in card.columns or 'Amount' not in card.columns:
        st.error("❌ Required columns ('Time', 'Class', 'Amount') are missing in the dataset.")
        st.stop()

    # Add hour column for time-based analysis
    card['Hour'] = (card['Time'] // 3600) % 24
    fraud = card[card['Class'] == 1]
    normal = card[card['Class'] == 0]

    if section == "Upload Data":
        st.success("✅ Dataset loaded successfully!")
        st.subheader("📊 Full Dataset Preview")
        AgGrid(card.head(500))
        st.markdown(f"📋 **Total Rows:** `{card.shape[0]}`")
        st.markdown(f"📋 **Total Columns:** `{card.shape[1]}`")

    elif section == "Overview Stats":
        st.subheader("📈 Summary Statistics")
        col1, col2 = st.columns(2)
        col1.metric("🔴 Fraud Transactions", len(fraud))
        col2.metric("🟢 Normal Transactions", len(normal))

        st.markdown("### 📌 Transaction Index Ranges")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("🔴 **Fraud Transaction Ranges**")
            fraud_ranges = get_contiguous_ranges(sorted(fraud.index.tolist()))
            st.write([f"{start} to {end}" for start, end in fraud_ranges] or "No fraud transactions found.")

        with col2:
            st.markdown("🟢 **Normal Transaction Ranges**")
            normal_ranges = get_contiguous_ranges(sorted(normal.index.tolist()))
            st.write([f"{start} to {end}" for start, end in normal_ranges] or "No normal transactions found.")

    elif section == "Index Viewer":
        st.subheader("🔍 View Transactions by Index Range")
        col1, col2 = st.columns(2)
        start_index = int(col1.number_input("Start Index", min_value=0, max_value=len(card) - 1, value=0))
        end_index = int(col2.number_input("End Index", min_value=0, max_value=len(card) - 1, value=10))

        if start_index <= end_index:
            subset = card.iloc[start_index:end_index + 1]
            st.write(f"Showing transactions from **index {start_index} to {end_index}**")
            AgGrid(subset)

            st.subheader("🧾 Transaction Fraud Status")
            for i, row in subset.iterrows():
                status = "FRAUD" if row["Class"] == 1 else "NORMAL"
                color = "🔴" if row["Class"] == 1 else "🟢"
                st.write(f"{color} Row {i}: **{status}** transaction")
        else:
            st.warning("⚠️ End index must be greater than or equal to start index.")

    elif section == "Visualizations":
        st.subheader("📊 Visual Insights")
        tab1, tab2, tab3 = st.tabs(["📊 Hourly Distribution", "💰 Amount Filter", "🥧 Class Pie Chart"])

        with tab1:
            st.markdown("### 🕒 Hourly Distribution of Fraud Transactions")
            hourly_fraud = fraud['Hour'].value_counts().sort_index()
            st.bar_chart(hourly_fraud)

        with tab2:
            st.markdown("### 💰 Filter by Transaction Amount")
            col1, col2 = st.columns(2)
            amount_min = col1.number_input("Minimum Amount", 0.0, float(card['Amount'].max()), 0.0)
            amount_max = col2.number_input("Maximum Amount", 0.0, float(card['Amount'].max()), 1000.0)

            if amount_min <= amount_max:
                filtered = card[(card['Amount'] >= amount_min) & (card['Amount'] <= amount_max)]
                st.write(f"Filtered {len(filtered)} transactions in amount range")
                AgGrid(filtered.head(500))
                csv = filtered.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download Filtered Data", data=csv, file_name="filtered_data.csv", mime='text/csv')
            else:
                st.warning("⚠️ Maximum amount must be greater than or equal to minimum amount.")

        with tab3:
            st.markdown("### 🥧 Class Distribution Pie Chart")
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.pie([len(fraud), len(normal)], labels=["Fraud", "Normal"],
                   autopct='%1.1f%%', colors=["red", "green"])
            ax.axis('equal')
            st.pyplot(fig)

else:
    st.info("📂 Please upload the `creditcard.csv` file to continue.")
