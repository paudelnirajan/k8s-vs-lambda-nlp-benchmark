import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import subprocess
import os
import concurrent.futures
from dotenv import load_dotenv
import re
import json

# Import Groq client
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# --- Configuration & Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
LOCUST_FILE = os.path.join(PROJECT_ROOT, "load-testing", "locust", "locustfile.py")
LOCUST_RESULTS_PREFIX = "locust_results"
LOCUST_REPORT_FILE = os.path.join(PROJECT_ROOT, "benchmark_report.html")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Page Configuration ---
st.set_page_config(
    page_title="NLP Deployment Benchmark",
    layout="wide"
)

# --- Session State Initialization ---
if "benchmark_running" not in st.session_state:
    st.session_state.benchmark_running = False
if "benchmark_complete" not in st.session_state:
    st.session_state.benchmark_complete = False
if "ai_analysis_result" not in st.session_state:
    st.session_state.ai_analysis_result = None

# --- Helper Functions ---
def analyze_text(text, deployment):
    """Send a single prediction request to the backend."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/analyze",
            json={"text": text, "deployment": deployment},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def fetch_metrics():
    """Fetch Prometheus metrics from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/metrics", timeout=10)
        return response.text
    except Exception as e:
        return f"Error fetching metrics: {str(e)}"

def run_script(script_name):
    """Run a shell script and return clean output."""
    script_path = os.path.join(PROJECT_ROOT, "scripts", script_name)
    try:
        # Run script with PROJECT_ROOT as working directory
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=300
        )
        
        def clean_output(text):
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', text)

        stdout_clean = clean_output(result.stdout)
        stderr_clean = clean_output(result.stderr)
        
        return {
            "success": result.returncode == 0,
            "code": result.returncode,
            "stdout": stdout_clean,
            "stderr": stderr_clean
        }
    except Exception as e:
        return {
            "success": False,
            "code": -1,
            "stdout": "",
            "stderr": str(e)
        }

def display_results_card(result, duration, label):
    """Display analysis results in a nice card format."""
    st.markdown(f"### {label}")
    if "error" in result:
        st.error(f"Failed: {result['error']}")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Sentiment", result.get("sentiment", "N/A"), delta=f"{result.get('confidence', 0):.2%}")
        c1.metric("Backend Latency", f"{result.get('response_time_ms', 0):.2f} ms", help="Time spent processing inside the Python app.")
        
        c2.metric("Round Trip", f"{duration * 1000:.2f} ms", help="Total time including network overhead.")
        c2.metric("Retries", result.get("retry_attempts", 0), help="Number of backend retries (e.g. for cold starts).")

def generate_ai_analysis(csv_path, users, spawn_rate):
    """Generate detailed analysis using Groq (Llama 3)."""
    if not HAS_GROQ or not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not found or 'groq' package not installed."
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        df = pd.read_csv(csv_path)
        csv_string = df.to_string()
        
        prompt = f"""
        You are a Senior Site Reliability Engineer (SRE) conducting a critical performance review of an NLP Sentiment Analysis service.
        
        **Test Configuration:**
        - **Concurrent Users:** {users}
        - **Spawn Rate:** {spawn_rate} users/sec
        - **Architectures Tested:** AWS Lambda (Serverless) vs AWS EKS (Kubernetes)
        
        **Raw Performance Data (Locust Stats):**
        {csv_string}
        
        **Task:**
        Provide a comprehensive, critical analysis report. Do not hold back on technical details.
        
        **Report Structure:**
        1.  **Executive Summary:** The "TL;DR" winner for this specific load pattern.
        2.  **Latency Analysis:** Compare Mean, 95th %ile, and Max latency. Explain *why* one might be slower (e.g., Lambda cold starts vs Container warm-up).
        3.  **Throughput & Stability:** Analyze RPS (Requests Per Second) and Failure Rates. Did any architecture buckle under load?
        4.  **Scalability Assessment:** Based on the user count ({users}), how did the systems handle concurrency?
        5.  **Final Recommendation:** When should we use Lambda? When should we use Kubernetes? Base this strictly on the data provided.
        
        Format the output using clean Markdown with bolding and bullet points for readability.
        """
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Analysis Failed: {str(e)}"

def render_charts_from_csv():
    """Render the comparison charts from the existing CSV file."""
    stats_file = os.path.join(PROJECT_ROOT, f"{LOCUST_RESULTS_PREFIX}_stats.csv")
    if os.path.exists(stats_file) and os.path.getsize(stats_file) > 0:
        try:
            df = pd.read_csv(stats_file)
            df_l = df[df["Name"] == "/analyze_lambda"]
            df_k = df[df["Name"] == "/analyze_kubernetes"]
            
            if not df_l.empty and not df_k.empty:
                comp_df = pd.DataFrame({
                    "Infrastructure": ["Lambda", "Kubernetes"],
                    "Avg Latency (ms)": [df_l.iloc[0]["Average Response Time"], df_k.iloc[0]["Average Response Time"]],
                    "RPS": [df_l.iloc[0]["Requests/s"], df_k.iloc[0]["Requests/s"]],
                    "P95 Latency (ms)": [df_l.iloc[0]["95%"], df_k.iloc[0]["95%"]]
                })
                
                c1, c2 = st.columns(2)
                with c1:
                    fig_lat = px.bar(
                        comp_df, x="Infrastructure", y="Avg Latency (ms)",
                        color="Infrastructure", title="Average Latency (Lower is Better)",
                        text_auto=True
                    )
                    st.plotly_chart(fig_lat, use_container_width=True)
                
                with c2:
                    fig_rps = px.bar(
                        comp_df, x="Infrastructure", y="RPS",
                        color="Infrastructure", title="Throughput (Requests/Sec - Higher is Better)",
                        text_auto=True
                    )
                    st.plotly_chart(fig_rps, use_container_width=True)
                
                # Summary Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Lambda Avg Latency", f"{df_l.iloc[0]['Average Response Time']:.0f} ms")
                m2.metric("K8s Avg Latency", f"{df_k.iloc[0]['Average Response Time']:.0f} ms")
                m3.metric("Lambda Failures", f"{df_l.iloc[0]['Failure Count']}")
                m4.metric("K8s Failures", f"{df_k.iloc[0]['Failure Count']}")
                
        except Exception:
            st.warning("Could not render charts from existing data.")

# --- UI Layout ---
st.title("Serverless vs Kubernetes Benchmark")
st.markdown(f"**Backend URL:** `{BACKEND_URL}`")

with st.expander("Metrics Guide"):
    st.markdown("""
    *   **Backend Latency**: The time the actual Python inference code took to run. This excludes network travel time.
    *   **Round Trip Time**: The total time from when you clicked the button until the result appeared.
    *   **RPS (Requests Per Second)**: Throughput of the system. Higher is better.
    """)

tab_analyze, tab_load_test, tab_scripts = st.tabs([
    "Live Comparison", 
    "Load Benchmark", 
    "Tools"
])

# --- TAB 1: Analyze Text ---
with tab_analyze:
    st.header("Head-to-Head Comparison")
    st.write("Send a request to both architectures simultaneously to compare cold starts and latency.")

    col1, col2 = st.columns([2, 1])
    with col1:
        text_input = st.text_area("Input Text", "The system architecture is truly fascinating and scalable!", height=100)
    with col2:
        deployment_mode = st.radio("Mode", ["Compare Both (Parallel)", "Lambda Only", "Kubernetes Only"])
        submit_btn = st.button("Analyze Sentiment", type="primary", use_container_width=True)

    if submit_btn and text_input:
        if deployment_mode == "Compare Both (Parallel)":
            with st.spinner("Running parallel requests..."):
                def timed_request(d):
                    s = time.time()
                    r = analyze_text(text_input, d)
                    return r, time.time() - s

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    f1 = executor.submit(timed_request, "lambda")
                    f2 = executor.submit(timed_request, "kubernetes")
                    res_lambda, dur_lambda = f1.result()
                    res_k8s, dur_k8s = f2.result()
            
            st.markdown("---")
            col_l, col_k = st.columns(2)
            with col_l:
                st.info("AWS Lambda")
                display_results_card(res_lambda, dur_lambda, "Lambda")
            with col_k:
                st.info("Kubernetes (EKS)")
                display_results_card(res_k8s, dur_k8s, "Kubernetes")
                
        else:
            target = "lambda" if "Lambda" in deployment_mode else "kubernetes"
            with st.spinner(f"Requesting {target}..."):
                s = time.time()
                res = analyze_text(text_input, target)
                dur = time.time() - s
            display_results_card(res, dur, deployment_mode)
            if "error" not in res:
                st.json(res)

# --- TAB 2: Load Testing (Locust) ---
with tab_load_test:
    st.header("Distributed Load Benchmark")
    st.write("Simulate traffic to compare how both systems scale under load.")

    with st.form("locust_config"):
        c1, c2, c3 = st.columns(3)
        users = c1.number_input("Concurrent Users", 1, 1000, 10)
        spawn_rate = c2.number_input("Spawn Rate (users/s)", 1, 100, 2)
        duration = c3.text_input("Duration", "30s")
        
        # Callback to start benchmark
        submitted = st.form_submit_button("Start Benchmark", type="primary")
        if submitted:
            st.session_state.benchmark_running = True
            st.session_state.benchmark_complete = False
            st.session_state.ai_analysis_result = None  # Reset analysis

    # Layout for live metrics
    st.markdown("### Live Metrics")
    live_col_l, live_col_k = st.columns(2)
    
    # Placeholders for live updates
    lambda_placeholder = live_col_l.empty()
    k8s_placeholder = live_col_k.empty()
    chart_placeholder = st.empty()
    
    # --- Benchmark Execution Logic ---
    if st.session_state.benchmark_running:
        # Cleanup previous run files
        for ext in ["_stats.csv", "_stats_history.csv"]:
            try:
                os.remove(os.path.join(PROJECT_ROOT, f"{LOCUST_RESULTS_PREFIX}{ext}"))
            except OSError: pass
        
        if os.path.exists(LOCUST_REPORT_FILE):
            try:
                os.remove(LOCUST_REPORT_FILE)
            except OSError: pass

        cmd = [
            "locust", "-f", LOCUST_FILE, "--headless",
            "-u", str(users), "-r", str(spawn_rate), "-t", duration,
            "--csv", LOCUST_RESULTS_PREFIX, 
            "--html", LOCUST_REPORT_FILE,
            "--host", BACKEND_URL
        ]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=PROJECT_ROOT)
            
            with st.spinner("Benchmarking in progress..."):
                while process.poll() is None:
                    time.sleep(1)
                    
                    stats_file = os.path.join(PROJECT_ROOT, f"{LOCUST_RESULTS_PREFIX}_stats.csv")
                    if os.path.exists(stats_file) and os.path.getsize(stats_file) > 0:
                        try:
                            df = pd.read_csv(stats_file)
                            df_l = df[df["Name"] == "/analyze_lambda"]
                            df_k = df[df["Name"] == "/analyze_kubernetes"]
                            
                            if not df_l.empty:
                                with lambda_placeholder.container():
                                    st.markdown("#### AWS Lambda Performance")
                                    l_row = df_l.iloc[0]
                                    c1, c2 = st.columns(2)
                                    c1.metric("Avg Latency", f"{l_row['Average Response Time']:.0f} ms")
                                    c2.metric("RPS", f"{l_row['Requests/s']:.1f}")
                                    st.metric("Failures", f"{l_row['Failure Count']}")

                            if not df_k.empty:
                                with k8s_placeholder.container():
                                    st.markdown("#### Kubernetes Performance")
                                    k_row = df_k.iloc[0]
                                    c1, c2 = st.columns(2)
                                    c1.metric("Avg Latency", f"{k_row['Average Response Time']:.0f} ms")
                                    c2.metric("RPS", f"{k_row['Requests/s']:.1f}")
                                    st.metric("Failures", f"{k_row['Failure Count']}")

                            if not df_l.empty and not df_k.empty:
                                comp_df = pd.DataFrame({
                                    "Infrastructure": ["Lambda", "Kubernetes"],
                                    "Avg Latency (ms)": [df_l.iloc[0]["Average Response Time"], df_k.iloc[0]["Average Response Time"]],
                                    "RPS": [df_l.iloc[0]["Requests/s"], df_k.iloc[0]["Requests/s"]]
                                })
                                fig = px.bar(comp_df, x="Infrastructure", y="Avg Latency (ms)", color="Infrastructure", title="Real-time Comparison")
                                chart_placeholder.plotly_chart(fig, use_container_width=True)

                        except Exception: pass
            
            if process.returncode == 0:
                st.session_state.benchmark_running = False
                st.session_state.benchmark_complete = True
                st.success("Benchmark Complete!")
                st.rerun()
            else:
                st.session_state.benchmark_running = False
                st.error("Benchmark finished with errors.")

        except Exception as e:
            st.session_state.benchmark_running = False
            st.error(f"Error: {e}")

    # --- Results Section (Persistent) ---
    if st.session_state.benchmark_complete:
        st.markdown("---")
        st.subheader("Benchmark Results & Analysis")
        
        # 1. Re-render the charts so they stay visible
        render_charts_from_csv()
        
        st.markdown("---")
        
        # 2. Analysis Controls
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            if os.path.exists(LOCUST_REPORT_FILE):
                with open(LOCUST_REPORT_FILE, "rb") as f:
                    st.download_button(
                        label="Download Detailed HTML Report",
                        data=f,
                        file_name="benchmark_report.html",
                        mime="text/html"
                    )
        
        with res_col2:
            # Only show button if we haven't analyzed yet
            if st.session_state.ai_analysis_result is None:
                if st.button("Generate AI Analysis Report (Groq)"):
                    stats_csv = os.path.join(PROJECT_ROOT, f"{LOCUST_RESULTS_PREFIX}_stats.csv")
                    if os.path.exists(stats_csv):
                        with st.spinner("Consulting AI Expert..."):
                            analysis = generate_ai_analysis(stats_csv, users, spawn_rate)
                            st.session_state.ai_analysis_result = analysis
                            st.rerun()
                    else:
                        st.error("Stats file not found. Run benchmark first.")
        
        # 3. Display AI Analysis in a distinct container
        if st.session_state.ai_analysis_result:
            with st.container():
                st.markdown("### 🤖 Critical Performance Analysis")
                st.info("Generated by Llama-3.3-70b-versatile based on current run data.")
                st.markdown(st.session_state.ai_analysis_result)
                
                if st.button("Clear Analysis"):
                    st.session_state.ai_analysis_result = None
                    st.rerun()

# --- TAB 3: Scripts ---
with tab_scripts:
    st.header("Scripts & Observability")
    
    col_s, col_m = st.columns(2)
    with col_s:
        st.subheader("Run Maintenance Scripts")
        
        # Script 1: Real API Tests
        if st.button("Run Real API Integration Tests"):
            with st.spinner("Running tests (pytest)..."):
                res = run_script("run-realAPI-tests.sh")
                
                if res["success"]:
                    st.success("Tests Passed!")
                else:
                    st.error(f"Tests Failed (Exit Code: {res['code']})")
                
                with st.expander("View Execution Logs", expanded=True):
                    st.text_area("Standard Output", res["stdout"], height=300)
                    if res["stderr"]:
                        st.text_area("Errors", res["stderr"], height=150)

        # Script 2: Metrics Fetcher
        if st.button("Run Metrics Script"):
            with st.spinner("Fetching endpoint metrics..."):
                res = run_script("run-metrics.sh")
                
                if res["success"]:
                    st.success("Metrics Fetched Successfully!")
                else:
                    st.error("Failed to fetch metrics")
                    
                with st.expander("View Metrics Output", expanded=True):
                    st.text_area("Output", res["stdout"], height=400)

    with col_m:
        st.subheader("Backend Observability")
        st.write("View raw metrics exposed by the orchestrator backend.")
        if st.button("Fetch Prometheus Metrics"):
            metrics = fetch_metrics()
            st.text_area("Raw Prometheus Data", metrics, height=500, help="Copy this into a Prometheus server to visualize.")