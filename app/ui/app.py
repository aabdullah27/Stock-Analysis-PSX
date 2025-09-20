import streamlit as st
import requests
import re
import time

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
SCRAPE_ENDPOINT = f"{API_BASE_URL}/analysis/scrape"
ANALYZE_ENDPOINT = f"{API_BASE_URL}/analysis/analyze"

st.set_page_config(page_title="Stocks FundaAnalytics", layout="wide", initial_sidebar_state="expanded")

# --- Initialize Session State ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "scraped_files" not in st.session_state:
    st.session_state.scraped_files = None
if "report" not in st.session_state:
    st.session_state.report = None
if "error" not in st.session_state:
    st.session_state.error = None
if "ui_step" not in st.session_state:
    st.session_state.ui_step = "input" # 'input', 'scraped', 'analyzed'
if "scrape_duration_seconds" not in st.session_state:
    st.session_state.scrape_duration_seconds = None
if "analysis_duration_seconds" not in st.session_state:
    st.session_state.analysis_duration_seconds = None

# --- Helper Functions ---
def clean_symbols(text):
    if not text: return []
    return re.findall(r'[A-Z0-9]+', text.upper())

def reset_session():
    st.session_state.session_id = None
    st.session_state.scraped_files = None
    st.session_state.report = None
    st.session_state.error = None
    st.session_state.ui_step = "input"
    st.session_state.scrape_duration_seconds = None
    st.session_state.analysis_duration_seconds = None

# --- Sidebar ---
with st.sidebar:
    st.image("https://i.imgur.com/bLd2i22.png", width=100) # Placeholder logo
    st.header("FundaAnalytics AI")
    st.markdown("A robust, two-step AI system for PSX stock analysis.")
    st.markdown("---")

    if st.button("Start New Analysis", use_container_width=True):
        reset_session()
        st.rerun()
    
    st.markdown("---")
    st.subheader("How it works:")
    st.info("""
    1.  **Scrape Data:** The system first gathers raw data from financial websites.
    2.  **Analyze Data:** An AI agent then analyzes these files, enriched with a live web search, to produce a final report.
    """)


# --- Main UI ---
st.title("📈 AI-Powered Stock Analysis")

# Step 1: Input Symbols and Scrape
if st.session_state.ui_step == "input":
    st.subheader("Step 1: Gather Market Data")
    with st.form("scrape_form"):
        symbols_input = st.text_input(
            "Enter up to 5 PSX Stock Symbols (comma or space-separated)",
            placeholder="e.g., ENGRO, HUBC, MCB, OGDC, LUCK"
        )
        scrape_button = st.form_submit_button("Gather Data", use_container_width=True)

    if scrape_button:
        symbols_list = clean_symbols(symbols_input)
        if not symbols_list:
            st.error("Please enter at least one valid stock symbol.")
        elif len(symbols_list) > 5:
            st.warning("Max 5 symbols allowed. Using the first 5.")
            symbols_list = symbols_list[:5]
        else:
            with st.spinner(f"Scraping data for {', '.join(symbols_list)}... This can take a few minutes."):
                try:
                    payload = {"symbols": symbols_list}
                    response = requests.post(SCRAPE_ENDPOINT, json=payload, timeout=600)
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.session_id = data["session_id"]
                        st.session_state.scraped_files = data["scraped_files"]
                        st.session_state.scrape_duration_seconds = data.get("duration_seconds")
                        st.session_state.ui_step = "scraped"
                        st.rerun()
                    else:
                        st.error(f"Error during scraping: {response.json().get('detail')}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection Error: Could not connect to the backend. Is it running? Details: {e}")

# Step 2: Display Scraped Files and Offer Analysis
if st.session_state.ui_step == "scraped":
    st.subheader("Step 1: Data Gathering Complete")
    if st.session_state.scrape_duration_seconds is not None:
        st.info(f"Scrape + upload time: {st.session_state.scrape_duration_seconds}s")
    st.success(f"Successfully scraped data for session `{st.session_state.session_id[:8]}`.")
    for symbol, files in st.session_state.scraped_files.items():
        with st.expander(f"📁 {symbol} - {len(files)} files gathered"):
            st.write(files)
    
    st.subheader("Step 2: Analyze the Gathered Data")
    analyze_button = st.button("✨ Run AI Analysis", use_container_width=True, type="primary")

    if analyze_button:
        with st.spinner("AI agents are analyzing the data... This involves multiple steps and may take some time."):
            try:
                payload = {"session_id": st.session_state.session_id}
                response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=600)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.report = data.get("report")
                    st.session_state.analysis_duration_seconds = data.get("duration_seconds")
                    st.session_state.ui_step = "analyzed"
                    st.rerun()
                else:
                    st.session_state.error = f"Error during analysis: {response.json().get('detail')}"
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.session_state.error = f"Connection Error during analysis: {e}"
                st.rerun()

# Step 3: Display Final Report or Error
if st.session_state.ui_step == "analyzed":
    st.subheader("Step 3: Analysis Complete")
    if st.session_state.analysis_duration_seconds is not None:
        st.info(f"Analysis time: {st.session_state.analysis_duration_seconds}s")
    if st.session_state.report:
        st.markdown(st.session_state.report)
    if st.session_state.error:
        st.error(st.session_state.error)