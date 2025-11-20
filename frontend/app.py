import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import concurrent.futures
import statistics

# Page Configuration
st.set_page_config(
    page_title="NLP Deployment Benchmark",
    page_icon="👎👍",
    layout="wide"
)

# Configuration
BACKEND_URL = "http://localhost:8000"
LAMBDA_COST_PER_1M = 0.20 + (3 * 0.0000166667 * 1_000_000 * 0.150) # Approx
EKS_MONTHLY_COST = 73.00 + 15.00 # Control plane + Node

# --- Helper Functions ---
def analyze_text(text, deployment):
    try:
        response = requests.post(
            f"{BACKEND_URL}/analyze",
            json={"text": text, "deployment": deployment},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def run_load_test(text, deployment, count, concurrency):
    latencies = []
    errors = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(analyze_text, text, deployment) 
            for _ in range(count)
        ]
        
        progress_bar = st.progress(0)
        completed = 0
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            completed += 1
            progress_bar.progress(completed / count)
            
            if "error" not in result:
                latencies.append(result.get("response_time_ms", 0) / 1000.0)
            else:
                errors += 1
                
    return latencies, errors

# --- Sidebar ---
with st.sidebar:
    st.title("Configuration")
    st.markdown("### Test Settings")
    deployment_mode = st.radio(
        "Select Mode",
        ["Single Prediction", "Benchmark Comparison"]
    )
    
    if deployment_mode == "Benchmark Comparison":
        num_requests = st.slider("Number of Requests", 10, 500, 50)
        concurrency = st.slider("Concurrency", 1, 20, 5)

# --- Main Content ---
st.title("NLP Sentiment Analysis Benchmark")
st.markdown("Compare **Serverless (AWS Lambda)** vs **Kubernetes (EKS)** performance and cost.")

if deployment_mode == "Single Prediction":
    st.subheader("Live Prediction")
    
    col1, col2 = st.columns(2)
    with col1:
        text_input = st.text_area("Enter text to analyze", "I absolutely love this new deployment architecture!", height=150)
        target = st.selectbox("Target Infrastructure", ["lambda", "kubernetes"])
        
        if st.button("Analyze Sentiment", type="primary"):
            with st.spinner(f"Sending request to {target.upper()}..."):
                start = time.time()
                result = analyze_text(text_input, target)
                duration = time.time() - start
                
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.success("Analysis Complete!")
                
                # Display Result
                res_col1, res_col2, res_col3 = st.columns(3)
                with res_col1:
                    st.metric("Sentiment", result["sentiment"], delta=f"{result['confidence']:.4f}")
                with res_col2:
                    st.metric("Latency (Backend)", f"{result['response_time_ms']:.2f}ms")
                with res_col3:
                    st.metric("Total Round Trip", f"{duration*1000:.2f}ms")
                
                # JSON View
                with st.expander("View Raw JSON Response"):
                    st.json(result)

elif deployment_mode == "Benchmark Comparison":
    st.subheader("⚔️ The Showdown: Lambda vs Kubernetes")
    
    benchmark_text = st.text_input("Benchmark Text", "This is a test for benchmarking latency.")
    
    if st.button("Start Benchmark", type="primary"):
        st.markdown("---")
        
        # Columns for live results
        col_lambda, col_k8s = st.columns(2)
        
        # 1. Run Lambda Benchmark
        with col_lambda:
            st.info("⚡ Running AWS Lambda Benchmark...")
            lambda_lats, lambda_errs = run_load_test(benchmark_text, "lambda", num_requests, concurrency)
            
            if lambda_lats:
                lambda_avg = statistics.mean(lambda_lats)
                lambda_p95 = statistics.quantiles(lambda_lats, n=20)[18]
                st.success(f"Done! Avg: {lambda_avg:.4f}s")
            else:
                st.error("Lambda Failed completely.")
                lambda_avg = 0

        # 2. Run Kubernetes Benchmark
        with col_k8s:
            st.info("☸️ Running Kubernetes Benchmark...")
            k8s_lats, k8s_errs = run_load_test(benchmark_text, "kubernetes", num_requests, concurrency)
            
            if k8s_lats:
                k8s_avg = statistics.mean(k8s_lats)
                k8s_p95 = statistics.quantiles(k8s_lats, n=20)[18]
                st.success(f"Done! Avg: {k8s_avg:.4f}s")
            else:
                st.error("Kubernetes Failed completely.")
                k8s_avg = 0

        # --- Analysis & Charts ---
        st.markdown("---")
        st.subheader("📊 Results Analysis")
        
        if lambda_lats and k8s_lats:
            # Data Frame for Charts
            df = pd.DataFrame({
                "Infrastructure": ["Lambda", "Kubernetes"] * 2,
                "Metric": ["Avg Latency", "Avg Latency", "P95 Latency", "P95 Latency"],
                "Value (s)": [lambda_avg, k8s_avg, lambda_p95, k8s_p95]
            })
            
            # Chart 1: Latency Comparison
            fig = px.bar(df, x="Infrastructure", y="Value (s)", color="Metric", barmode="group",
                         title="Latency Comparison (Lower is Better)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Stats Table
            st.markdown("### Detailed Statistics")
            stats_data = {
                "Metric": ["Requests", "Success", "Errors", "Avg Latency", "Min Latency", "Max Latency", "P95 Latency"],
                "AWS Lambda": [
                    num_requests, len(lambda_lats), lambda_errs, 
                    f"{lambda_avg:.4f}s", f"{min(lambda_lats):.4f}s", f"{max(lambda_lats):.4f}s", f"{lambda_p95:.4f}s"
                ],
                "Kubernetes": [
                    num_requests, len(k8s_lats), k8s_errs,
                    f"{k8s_avg:.4f}s", f"{min(k8s_lats):.4f}s", f"{max(k8s_lats):.4f}s", f"{k8s_p95:.4f}s"
                ]
            }
            st.table(pd.DataFrame(stats_data))
            
            # --- Recommendation Engine ---
            st.markdown("### 💡 Recommendation")
            
            winner = "Kubernetes" if k8s_avg < lambda_avg else "Lambda"
            diff = abs(lambda_avg - k8s_avg)
            ratio = lambda_avg / k8s_avg if winner == "Kubernetes" else k8s_avg / lambda_avg
            
            st.info(f"🏆 **Winner based on Speed:** {winner} ({ratio:.2f}x faster)")
            
            rec_col1, rec_col2 = st.columns(2)
            with rec_col1:
                st.markdown("#### 💰 Cost Analysis")
                st.write(f"- **Lambda**: ~${LAMBDA_COST_PER_1M:.4f} per 1M requests")
                st.write(f"- **Kubernetes**: ~${EKS_MONTHLY_COST:.2f} / month (Fixed)")
                st.write("**Verdict**: Lambda is 100x cheaper for low/sporadic traffic.")
                
            with rec_col2:
                st.markdown("#### 🧠 Context")
                if winner == "Lambda":
                    st.write("Lambda won! This is likely due to network overhead or resource constraints on the small K8s node.")
                else:
                    st.write("Kubernetes won! Once warm, containers are usually faster than Lambda cold starts.")
