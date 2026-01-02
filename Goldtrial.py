import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. SETTINGS & PASSWORD ---
st.set_page_config(page_title="Gold Tracker Pro", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 Private Business Portal")
        pin = st.text_input("Enter Access PIN", type="password")
        if st.button("Unlock"):
            if pin == "1234": # Change your PIN here
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Invalid PIN")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. DATA STORAGE ---
CSV_FILE = "data.csv"
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=["Date", "Grams", "Cost"])

df = load_data()

# --- 3. SIDEBAR INPUTS ---
with st.sidebar:
    st.header("➕ Add New Batch")
    with st.form("input_form", clear_on_submit=True):
        d = st.date_input("Purchase Date", datetime.date.today())
        g = st.number_input("Grams Bought", min_value=0.0, step=1.0)
        c = st.number_input("Total Purchasing Amount ($)", min_value=0.0, step=10.0)
        if st.form_submit_button("Save to Records"):
            new_row = pd.DataFrame([[str(d), g, c]], columns=["Date", "Grams", "Cost"])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.rerun()
    
    st.divider()
    st.header("💾 Maintenance")
    if st.button("🗑️ Clear All Data"):
        if os.path.exists(CSV_FILE): os.remove(CSV_FILE)
        st.rerun()

# --- 4. MAIN DASHBOARD ---
st.title("🏆 Gold Investment Dashboard")
m_price = st.number_input("Current Selling Gram Price ($/g)", value=193.0)

if not df.empty:
    # --- CALCULATION LOGIC ---
    calc_df = df.copy()
    calc_df['Date'] = pd.to_datetime(calc_df['Date'])
    
    # 1. Unit Price
    calc_df['Unit Price'] = calc_df['Cost'] / calc_df['Grams']
    
    # 2. Interest Calculation (10% Yearly)
    calc_df['Days Held'] = (pd.Timestamp.now() - calc_df['Date']).dt.days
    calc_df['Daily Int'] = (calc_df['Cost'] * 0.10) / 365
    calc_df['Acc_Interest'] = calc_df['Daily Int'] * calc_df['Days Held']
    
    # 3. Total Investment Value (Break-even point)
    calc_df['Total Value Today'] = calc_df['Cost'] + calc_df['Acc_Interest']
    
    # 4. Profit & Status
    calc_df['Selling Price'] = calc_df['Grams'] * m_price
    calc_df['Profit'] = calc_df['Selling Price'] - calc_df['Total Value Today']
    calc_df['Status'] = calc_df['Profit'].apply(lambda x: "✅ MATURED" if x > 0 else "❌ HOLD (LOSS)")

    # --- DISPLAY TABLE ---
    st.subheader("📋 Detailed Ledger")
    
    # Formatting for display
    display_table = calc_df.copy()
    display_table['Date'] = display_table['Date'].dt.date
    # Rounding numbers for clean look
    for col in ['Unit Price', 'Acc_Interest', 'Total Value Today', 'Selling Price', 'Profit']:
        display_table[col] = display_table[col].map('{:,.2f}'.format)

    st.dataframe(display_table[['Date', 'Grams', 'Cost', 'Unit Price', 'Days Held', 'Acc_Interest', 'Total Value Today', 'Selling Price', 'Profit', 'Status']], width='stretch')

    # --- DELETE INDIVIDUAL ROWS ---
    st.divider()
    st.subheader("🗑️ Delete Individual Batch")
    row_to_delete = st.selectbox("Select Date to Remove", options=calc_df.index, format_func=lambda x: f"Batch on {calc_df.iloc[x]['Date'].date()} ({calc_df.iloc[x]['Grams']}g)")
    if st.button("Delete Selected Batch"):
        df = df.drop(row_to_delete)
        df.to_csv(CSV_FILE, index=False)
        st.rerun()
else:
    st.info("No records found. Please enter your first batch in the sidebar.")
