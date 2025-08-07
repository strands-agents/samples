"""
Benchmark utilities for the LlamaCpp demo notebook.

This module contains functions for performance testing, analysis,
and visualization of different LlamaCpp configurations.
"""

import time
from typing import Dict, List, Any

from strands import Agent
from strands.models.llamacpp import LlamaCppModel


def benchmark_performance(prompt: str = "Explain quantum computing in simple terms.",
                         base_url: str = "http://localhost:8080",
                         runs_per_config: int = 5) -> List[Dict[str, Any]]:
    """
    Benchmark different performance settings with detailed analysis.
    
    Args:
        prompt: Prompt to use for benchmarking
        base_url: Base URL for the LlamaCpp server  
        runs_per_config: Number of runs per configuration for averaging
    
    Returns:
        List of benchmark results with comprehensive statistics
    """
    configs = [
        {
            "name": "Default (no optimization)",
            "params": {
                "temperature": 0.7,
                "max_tokens": 150
            }
        },
        {
            "name": "With prompt caching",
            "params": {
                "temperature": 0.7,
                "max_tokens": 150,
                "cache_prompt": True
            }
        },
        {
            "name": "Optimized sampling",
            "params": {
                "temperature": 0.7,
                "max_tokens": 150,
                "cache_prompt": True,
                "top_k": 30,
                "min_p": 0.05
            }
        },
        {
            "name": "Aggressive optimization",
            "params": {
                "temperature": 0.7,
                "max_tokens": 150,
                "cache_prompt": True,
                "top_k": 20,
                "min_p": 0.1,
                "repeat_penalty": 1.1,
                "n_probs": 0  # Don't compute token probabilities
            }
        }
    ]
    
    results = []
    
    print("Performance Benchmark")
    print("=" * 80)
    print(f"Prompt: {prompt}")
    print(f"Runs per config: {runs_per_config}")
    print("=" * 80)
    
    for config in configs:
        print(f"\nTesting: {config['name']}")
        print("-" * 40)
        
        # Ensure base_url doesn't have /v1 suffix to avoid double /v1 in URL  
        clean_base_url = base_url.rstrip('/').replace('/v1', '')
        model = LlamaCppModel(
            base_url=clean_base_url,
            params=config['params']
        )
        agent = Agent(model=model)
        
        # Warm-up run (not counted)
        _ = agent(prompt)
        
        # Actual benchmark runs
        times = []
        responses = []
        tokens_per_sec = []
        
        for i in range(runs_per_config):
            start = time.time()
            response = agent(prompt)
            elapsed = time.time() - start
            times.append(elapsed)
            
            # Extract text from response
            if hasattr(response, 'message') and 'content' in response.message:
                text_content = ""
                for content_block in response.message['content']:
                    if 'text' in content_block:
                        text_content += content_block['text']
                response_text = text_content.strip()
            else:
                response_text = str(response)
            
            responses.append(response_text)
            
            # Estimate tokens (rough approximation)
            token_count = len(response_text.split())
            tps = token_count / elapsed if elapsed > 0 else 0
            tokens_per_sec.append(tps)
            
            print(f"  Run {i+1}: {elapsed:.2f}s ({tps:.1f} tokens/s)")
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = (sum((t - avg_time) ** 2 for t in times) / len(times)) ** 0.5
        avg_tps = sum(tokens_per_sec) / len(tokens_per_sec)
        
        result = {
            "config": config['name'],
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_dev": std_dev,
            "times": times,
            "avg_tokens_per_sec": avg_tps,
            "params": config['params'],
            "responses": responses,
            "success_rate": 1.0
        }
        results.append(result)
        
        print(f"  Average: {avg_time:.2f}s ± {std_dev:.2f}s")
        print(f"  Range: [{min_time:.2f}s - {max_time:.2f}s]")
        print(f"  Avg tokens/s: {avg_tps:.1f}")
    
    print("\n" + "=" * 80)
    return results


def analyze_benchmark_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze benchmark results and provide performance insights.
    
    Args:
        results: List of benchmark results from benchmark_performance()
    
    Returns:
        Dictionary containing analysis results and recommendations
    """
    if not results:
        return {"error": "No valid benchmark results to analyze"}
    
    print("Performance Analysis")
    print("=" * 80)
    
    # Find baseline (default config)
    baseline = None
    for r in results:
        if "Default" in r['config']:
            baseline = r
            break
    
    if not baseline:
        baseline = results[0]  # Use first result as baseline
    
    baseline_time = baseline['avg_time']
    
    # Performance comparison table
    print("\nPerformance Comparison:")
    print("-" * 80)
    print(f"{'Configuration':<35} {'Avg Time':<12} {'Speedup':<10} {'Tokens/s':<12} {'Std Dev':<10}")
    print("-" * 80)
    
    for result in results:
        speedup = baseline_time / result['avg_time'] if result['avg_time'] > 0 else 0
        print(f"{result['config']:<35} {result['avg_time']:.2f}s{'':<6} "
              f"{speedup:.2f}x{'':<5} {result['avg_tokens_per_sec']:.1f}{'':<8} "
              f"±{result['std_dev']:.3f}s")
    
    # Find best configurations
    fastest = min(results, key=lambda x: x['avg_time']) if results else None
    most_consistent = min(results, key=lambda x: x['std_dev']) if results else None
    
    # Key findings
    print("\n" + "=" * 80)
    print("Key Findings:")
    print("-" * 80)
    
    if fastest:
        print(f"Fastest configuration: {fastest['config']}")
        print(f"   - Average time: {fastest['avg_time']:.2f}s")
        print(f"   - {(baseline_time / fastest['avg_time'] - 1) * 100:.1f}% faster than baseline")
        print(f"   - Tokens/s: {fastest['avg_tokens_per_sec']:.1f}")
    
    if most_consistent:
        print(f"\nMost consistent (lowest variance): {most_consistent['config']}")
        print(f"   - Standard deviation: ±{most_consistent['std_dev']:.3f}s")
        print(f"   - Success rate: {most_consistent['success_rate']:.1%}")
    
    # Parameter impact analysis
    print("\nParameter Impact Analysis:")
    for result in results:
        if result['config'] != baseline['config']:
            params = result['params']
            key_params = []
            if params.get('cache_prompt'):
                key_params.append("prompt caching")
            if params.get('top_k') and params['top_k'] < 40:
                key_params.append(f"top_k={params['top_k']}")
            if params.get('min_p'):
                key_params.append(f"min_p={params['min_p']}")
            if params.get('n_probs') == 0:
                key_params.append("no prob computation")
                
            if key_params:
                impact = (baseline_time - result['avg_time']) / baseline_time * 100
                print(f"   - {', '.join(key_params)}: {impact:+.1f}% performance")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("Recommendations:")
    print("-" * 80)
    print("1. Enable prompt caching for repeated queries (cache_prompt=True)")
    print("2. Use top_k=20-30 with min_p=0.05-0.1 for balanced quality/speed")
    print("3. Disable probability computation (n_probs=0) if not needed")
    print("4. Consider the trade-off between speed and output quality")
    print("5. Test configurations with your specific use case and model")
    
    analysis_results = {
        "baseline": baseline,
        "fastest": fastest,
        "most_consistent": most_consistent,
        "results": results,
        "recommendations": [
            "Enable prompt caching for repeated queries",
            "Use balanced sampling parameters (top_k=20-30, min_p=0.05-0.1)",
            "Disable probability computation if not needed",
            "Test configurations with your specific workload"
        ]
    }
    
    return analysis_results


def visualize_performance(results: List[Dict[str, Any]]) -> None:
    """
    Create text-based visualizations for performance comparison.
    
    Args:
        results: List of benchmark results from benchmark_performance()
    """
    if not results:
        print("No results to visualize")
        return
    
    print("\nPerformance Visualization")
    print("=" * 80)
    
    # Find max values for scaling
    max_time = max(r['avg_time'] for r in results)
    max_tps = max(r['avg_tokens_per_sec'] for r in results)
    bar_width = 50
    
    # Average response time chart
    print("\nAverage Response Time (lower is better):")
    print("-" * 80)
    
    for result in results:
        # Calculate bar length
        bar_length = int((result['avg_time'] / max_time) * bar_width)
        bar = '█' * bar_length
        
        # Format time and config name
        time_str = f"{result['avg_time']:.2f}s"
        config_name = result['config'][:25] + "..." if len(result['config']) > 25 else result['config']
        
        print(f"{config_name:<30} {bar:<{bar_width}} {time_str}")
    
    print("-" * 80)
    
    # Tokens per second comparison
    print("\nTokens per Second (higher is better):")
    print("-" * 80)
    
    for result in results:
        # Calculate bar length  
        bar_length = int((result['avg_tokens_per_sec'] / max_tps) * bar_width) if max_tps > 0 else 0
        bar = '▓' * bar_length
        
        # Format tokens/s and config name
        tps_str = f"{result['avg_tokens_per_sec']:.1f} tokens/s"
        config_name = result['config'][:25] + "..." if len(result['config']) > 25 else result['config']
        
        print(f"{config_name:<30} {bar:<{bar_width}} {tps_str}")
    
    print("-" * 80)
    
    # Consistency comparison (standard deviation)
    print("\nConsistency (lower standard deviation is better):")
    print("-" * 80)
    
    max_std = max(r['std_dev'] for r in results)
    
    for result in results:
        # Calculate bar length (inverted - shorter bars are better)
        bar_length = int((result['std_dev'] / max_std) * bar_width) if max_std > 0 else 0
        bar = '░' * bar_length
        
        # Format std dev and config name
        std_str = f"±{result['std_dev']:.3f}s"
        config_name = result['config'][:25] + "..." if len(result['config']) > 25 else result['config']
        
        print(f"{config_name:<30} {bar:<{bar_width}} {std_str}")
    
    print("-" * 80)


def run_comprehensive_benchmark(base_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """
    Run a comprehensive benchmark suite and analysis.
    
    Args:
        base_url: Base URL for the LlamaCpp server
    
    Returns:
        Complete benchmark results and analysis
    """
    print("Comprehensive LlamaCpp Performance Benchmark")
    print("=" * 90)
    
    # Run benchmark
    results = benchmark_performance(base_url=base_url)
    
    if not results:
        print("No valid benchmark results obtained")
        return {"error": "Benchmark failed"}
    
    # Analyze results
    analysis = analyze_benchmark_results(results)
    
    # Visualize results
    visualize_performance(results)
    
    return {
        "benchmark_results": results,
        "analysis": analysis,
        "summary": {
            "total_configs_tested": len(results),
            "fastest_config": analysis.get("fastest", {}).get("config", "Unknown"),
            "best_speedup": f"{(analysis['baseline']['avg_time'] / analysis['fastest']['avg_time']):.2f}x" if analysis.get("fastest") else "N/A",
            "recommendations": analysis.get("recommendations", [])
        }
    }