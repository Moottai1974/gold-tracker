import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. PASSWORD PROTECTION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 Private Business Portal")
        password = st.text_input("Enter Access PIN", type="password")
        if st.button("Unlock"):
            if password == "131008":  # <--- CHANGE YOUR PIN HERE
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Invalid PIN")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. CONFIGURATION & DATA ---
st.set_page_config(page_title="Gold Tracker Pro", layout="wide")
st.title("🏆 Gold Investment Dashboard")

# Connect to Google Sheets (This keeps data alive on your phone!)
# Note: You will need to set up the connection in your Streamlit dashboard later
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(worksheet="Sheet1")
    except:
        return pd.DataFrame(columns=["Purchase Date", "Grams", "Total Cost"])

df = load_data()

# --- 3. CALCULATIONS ---
def calculate_metrics(df_input, current_price):
    if df_input.empty:
        return pd.DataFrame()
    
    temp_df = df_input.copy()
    temp_df['Purchase Date'] = pd.to_datetime(temp_df['Purchase Date'])
    temp_df['Days'] = (pd.Timestamp.now() - temp_df['Purchase Date']).dt.days
    
    # 10% Interest Calculation
    temp_df['Interest'] = (temp_df['Total Cost'] * 0.10 / 365) * temp_df['Days']
    temp_df['Break-even'] = temp_df['Total Cost'] + temp_df['Interest']
    
    # Profit Calculation
    temp_df['Value Now'] = temp_df['Grams'] * current_price
    temp_df['Profit'] = temp_df['Value Now'] - temp_df['Break-even']
    temp_df['Status'] = temp_df['Profit'].apply(lambda x: "✅ SELL" if x > 0 else "❌ HOLD")
    
    return temp_df

# --- 4. INPUT SIDEBAR ---
with st.sidebar:
    st.header("➕ Add New Purchase")
    with st.form("add_form", clear_on_submit=True):
        d = st.date_input("Date", datetime.date.today())
        g = st.number_input("Grams", min_value=0.0)
        c = st.number_input("Total Cost ($)", min_value=0.0)
        
        if st.form_submit_button("Save to Cloud"):
            new_row = pd.DataFrame([[str(d), g, c]], columns=["Purchase Date", "Grams", "Total Cost"])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("Synced with Cloud!")
            st.rerun()

    if st.button("🗑️ Clear All Records"):
        conn.update(worksheet="Sheet1", data=pd.DataFrame(columns=["Purchase Date", "Grams", "Total Cost"]))
        st.rerun()

# --- 5. MAIN DISPLAY ---
price = st.number_input("Current Market Price (SGD/g)", value=193.0)
display_df = calculate_metrics(df, price)

if not display_df.empty:
    st.subheader("📊 Your Portfolio")
    # Clean display for Mobile
    st.dataframe(display_df[['Purchase Date', 'Grams', 'Total Cost', 'Profit', 'Status']], width='stretch')
    
    # Ready to Sell alert
    matured = display_df[display_df['Profit'] > 0]
    if not matured.empty:
        st.balloons()
        st.success(f"🔥 {len(matured)} items are ready to sell for a profit!")
else:

    st.info("No data yet. Use the sidebar to add your first gold bar.")
