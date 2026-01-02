import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. SETTINGS & PASSWORD ---
st.set_page_config(page_title="Gold Tracker", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 Gold Business Login")
        pin = st.text_input("Enter PIN", type="password")
        if st.button("Login"):
            if pin == "1234": # <--- You can change this PIN
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Incorrect PIN")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. DATA HANDLING (Saves to a file named 'data.csv') ---
CSV_FILE = "data.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=["Date", "Grams", "Cost"])

df = load_data()

# --- 3. SIDEBAR INPUTS ---
with st.sidebar:
    st.header("➕ New Entry")
    with st.form("input_form", clear_on_submit=True):
        d = st.date_input("Purchase Date", datetime.date.today())
        g = st.number_input("Grams", min_value=0.0, step=1.0)
        c = st.number_input("Total Cost ($)", min_value=0.0, step=10.0)
        if st.form_submit_button("Save Entry"):
            new_row = pd.DataFrame([[str(d), g, c]], columns=["Date", "Grams", "Cost"])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.success("Saved!")
            st.rerun()
    
    st.divider()
    # BACKUP BUTTON (Very important for Plan B)
    st.header("💾 Backup")
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Excel/CSV", data=csv_bytes, file_name="gold_data_backup.csv", mime="text/csv")

# --- 4. MAIN DASHBOARD ---
st.title("🏆 Gold Portfolio")
m_price = st.number_input("Current Market Price ($/g)", value=230.0)

if not df.empty:
    # Calculations
    temp_df = df.copy()
    temp_df['Date'] = pd.to_datetime(temp_df['Date'])
    temp_df['Days'] = (pd.Timestamp.now() - temp_df['Date']).dt.days
    temp_df['Target(10%)'] = temp_df['Cost'] + (temp_df['Cost'] * 0.10 / 365 * temp_df['Days'])
    temp_df['CurrentValue'] = temp_df['Grams'] * m_price
    temp_df['Profit'] = temp_df['CurrentValue'] - temp_df['Target(10%)']
    
    # Display each item clearly for Mobile
    for index, row in temp_df.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Date:** {row['Date'].date()} | **Weight:** {row['Grams']}g")
                st.write(f"**Profit:** ${row['Profit']:,.2f}")
                status_color = "green" if row['Profit'] > 0 else "red"
                st.markdown(f"Status: :{status_color}[{'✅ READY TO SELL' if row['Profit'] > 0 else '❌ HOLD'}]")
            with col2:
                if st.button("🗑️", key=f"del_{index}"):
                    df = df.drop(index)
                    df.to_csv(CSV_FILE, index=False)
                    st.rerun()
else:
    st.info("No records yet. Add your first purchase in the sidebar.")
