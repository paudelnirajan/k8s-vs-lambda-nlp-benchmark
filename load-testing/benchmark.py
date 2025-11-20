import time
import requests
import statistics
import concurrent.futures
import sys
import os
from typing import List

# Add project root to python path so we can import model.logger_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.logger_config import get_logger

# Setup logger
logger = get_logger("benchmark")

# Configuration
BACKEND_URL = "http://localhost:8000/analyze"
NUM_REQUESTS = 10
CONCURRENCY = 5
TEST_TEXT = "I hate this!"

# Report file path
base_dir = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(base_dir, "results", "benchmark_results.txt")
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

def write_report(content: str):
    """Append content to the report file and log it."""
    # Log to console/main log file
    logger.info(content) 
    # Append to clean report file
    with open(REPORT_FILE, "a") as f:
        f.write(content + "\n")

def call_api(deployment_type: str) -> float:
    """Call the API and return latency in seconds."""
    start_time = time.time()
    try:
        response = requests.post(
            BACKEND_URL,
            json={"text": TEST_TEXT, "deployment": deployment_type},
            timeout=30
        )
        response.raise_for_status()
        return time.time() - start_time
    except Exception as e:
        logger.error(f"Request failed ({deployment_type}): {e}")
        return None

def run_benchmark(deployment_type: str) -> List[float]:
    logger.info(f"--- Starting Benchmarking for {deployment_type.upper()} ---")
    latencies = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(call_api, deployment_type) for _ in range(NUM_REQUESTS)]
        
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            latency = future.result()
            completed += 1
            if latency:
                latencies.append(latency)
                if completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{NUM_REQUESTS} requests completed")
    
    logger.info(f"Finished {deployment_type.upper()} benchmark.")
    return latencies

def log_stats(name: str, latencies: List[float]):
    if not latencies:
        write_report(f"{name}: No successful requests recorded.")
        return
    
    avg = statistics.mean(latencies)
    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18]
    min_val = min(latencies)
    max_val = max(latencies)

    first_3 = [f"{x:.4f}s" for x in latencies[:3]]
    last_3 = [f"{x:.4f}s" for x in latencies[-3:]] if len(latencies) > 3 else []
    
    # Format the stats block
    stats = (
        f"\nResults for {name}:\n"
        f"  Samples: {len(latencies)}\n"
        f"  Avg:     {avg:.4f}s\n"
        f"  Min:     {min_val:.4f}s\n"
        f"  Max:     {max_val:.4f}s\n"
        f"  P50:     {p50:.4f}s\n"
        f"  P95:     {p95:.4f}s\n"
        f"  First 3: {', '.join(first_3)}\n"
        f"  Last 3:  {', '.join(last_3)}\n"
    )
    write_report(stats)
    estimate_costs(name, avg)


LAMBDA_REQ_PRICE = 0.20 / 1_000_000
LAMBDA_GB_SEC_PRICE = 0.0000166667
LAMBDA_MEMORY_GB = 3.0

# EKS (Cluster + 1 t3.small node)
EKS_HOURLY_PRICE = 0.10
EC2_HOURLY_PRICE = 0.0208
TOTAL_EKS_HOURLY = EKS_HOURLY_PRICE + EC2_HOURLY_PRICE

def estimate_costs(name: str, avg_latency: float):
    """
    Estimate costs for 1 Million requests.
    
    For Lambda: Purely usage based.
    For EKS: Assumes we fully utilize the capacity (theoretical comparison)
             OR we show the fixed monthly cost.
    """
    
    cost_msg = ""
    
    if name == "AWS Lambda":
        # Cost = (Requests * ReqPrice) + (Requests * Duration * Memory * ComputePrice)
        compute_cost = 1_000_000 * avg_latency * LAMBDA_MEMORY_GB * LAMBDA_GB_SEC_PRICE
        req_cost = 1_000_000 * LAMBDA_REQ_PRICE
        total_1m = compute_cost + req_cost
        
        cost_msg = (
            f"Cost Estimation (AWS Lambda):\n"
            f"  Cost per 1M requests: ${total_1m:.4f}\n"
            f"  (Based on avg duration: {avg_latency:.4f}s @ 3GB RAM)\n"
            f"  Monthly Fixed Cost:   $0.00\n"
        )

    elif "Kubernetes" in name:
        # EKS is fixed cost per hour, regardless of requests (until you scale up)
        monthly_cost = TOTAL_EKS_HOURLY * 24 * 30
        
        # To compare apples-to-apples, we calculate "Cost per 1M requests"
        # assuming we are sending them continuously at the benchmark rate.
        # Throughput (req/sec) = 1 / avg_latency * Concurrency (approx)
        # This is a rough approximation.
        
        cost_msg = (
            f"Cost Estimation (EKS + t3.small):\n"
            f"  Monthly Fixed Cost:   ${monthly_cost:.2f} (regardless of traffic)\n"
            f"  Hourly Cost:          ${TOTAL_EKS_HOURLY:.4f}\n"
            f"  *Note: EKS is cheaper only if you have high sustained traffic.\n"
        )
        
    write_report(cost_msg)




def main():
    # Initialize report file
    with open(REPORT_FILE, "w") as f:
        f.write(f"Benchmark Report - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n")

    logger.info("Starting Comprehensive Benchmark Comparison...")
    logger.info(f"Configuration: Requests={NUM_REQUESTS}, Concurrency={CONCURRENCY}")
    
    # Benchmark Lambda
    lambda_latencies = run_benchmark("lambda")
    log_stats("AWS Lambda", lambda_latencies)
    
    # Benchmark Kubernetes
    k8s_latencies = run_benchmark("kubernetes")
    log_stats("Kubernetes (EKS)", k8s_latencies)

    # Comparison
    if lambda_latencies and k8s_latencies:
        lambda_avg = statistics.mean(lambda_latencies)
        k8s_avg = statistics.mean(k8s_latencies)
        
        verdict = "\n--- FINAL VERDICT ---\n"
        if k8s_avg < lambda_avg:
            speedup = lambda_avg / k8s_avg
            verdict += f"🏆 Kubernetes is the winner! ({speedup:.2f}x faster)"
        else:
            speedup = k8s_avg / lambda_avg
            verdict += f"🏆 AWS Lambda is the winner! ({speedup:.2f}x faster)"
        
        write_report(verdict)

if __name__ == "__main__":
    main()