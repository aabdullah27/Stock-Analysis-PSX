import streamlit as st
import requests
import re

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
ANALYSIS_ENDPOINT = f"{API_BASE_URL}/analysis/stocks"

st.set_page_config(page_title="Stocks FundaAnalytics", layout="wide")

# --- Helper Functions ---
def clean_symbols(text):
    """Cleans and extracts comma/space-separated stock symbols."""
    if not text:
        return []
    # Use regex to find all sequences of uppercase letters and numbers
    symbols = re.findall(r'[A-Z0-9]+', text.upper())
    return symbols

def check_backend_health():
    """Checks if the backend API is responsive."""
    try:
        response = requests.get(API_BASE_URL.replace("/api/v1", "/"), timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# --- UI Layout ---
st.title("📈 Stocks Fundamental Analysis Assistant")
st.markdown("Enter up to 5 PSX stock symbols (e.g., BOP, OGDC, LUCK) to receive an AI-generated fundamental analysis report.")

# --- Sidebar ---
with st.sidebar:
    st.header("Controls")
    backend_status = "🟢 Connected" if check_backend_health() else "🔴 Disconnected"
    st.metric("Backend Status", backend_status)
    st.info("Ensure the FastAPI backend is running for the app to function.")
    st.markdown("---")
    st.header("About")
    st.write("This application uses a system of AI agents to perform fundamental analysis on stocks from the Pakistan Stock Exchange (PSX).")

# --- Main Content Area ---
if 'last_report' not in st.session_state:
    st.session_state.last_report = ""

# Input form for stock symbols
with st.form("stock_input_form"):
    symbols_input = st.text_input(
        "Enter Stock Symbols (comma or space-separated)",
        placeholder="e.g., ENGRO, HUBC, MCB"
    )
    submitted = st.form_submit_button("Analyze Stocks")

if submitted:
    symbols_list = clean_symbols(symbols_input)
    if not symbols_list:
        st.error("Please enter at least one valid stock symbol.")
    elif len(symbols_list) > 5:
        st.warning("Analysis is limited to 5 stocks at a time. Analyzing the first 5 symbols provided.")
        symbols_list = symbols_list[:5]
    else:
        with st.spinner(f"🚀 Launching AI agents to analyze: {', '.join(symbols_list)}... This may take a few minutes."):
            try:
                payload = {"symbols": symbols_list}
                response = requests.post(ANALYSIS_ENDPOINT, json=payload, timeout=600) # 10-minute timeout

                if response.status_code == 200:
                    result = response.json()
                    st.session_state.last_report = result.get("report", "No report was generated.")
                else:
                    error_detail = response.json().get('detail', 'Unknown error')
                    st.session_state.last_report = f"❌ **Error:** Failed to get analysis. Status code: {response.status_code}\n\n**Details:** {error_detail}"

            except requests.exceptions.RequestException as e:
                st.session_state.last_report = f"❌ **Connection Error:** Could not connect to the backend. Please ensure it is running.\n\n**Details:** {e}"

# Display the report outside the form
if st.session_state.last_report:
    st.markdown("---")
    st.header("Analysis Report")
    st.markdown(st.session_state.last_report, unsafe_allow_html=True)
