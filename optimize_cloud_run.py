import subprocess
import json
 
def optimize_service(service_name, memory, cpu, max_instances, timeout):
    """Optimize individual Cloud Run service"""
    print(f"Optimizing {service_name}...")
    
    commands = [
        f"gcloud run services update {service_name}",
        f"--region=asia-east2",
        f"--memory={memory}",
        f"--cpu={cpu}",
        f"--max-instances={max_instances}",
        f"--timeout={timeout}",
        f"--quiet"
    ]
    
    cmd = " ".join(commands)
    print(f"Configuration: Memory={memory}, CPU={cpu}, Max Instances={max_instances}")
    
    # Note: User needs to run these commands manually
    print(f"Command to run: {cmd}")
 
def optimize_all_services():
    """Optimize all Cloud Run services"""
    print("⚡ CLOUD RUN OPTIMIZATION")
    print("=" * 30)
    
    # Optimized configurations
    services_config = [
        ("sentinel-api-service", "512Mi", "1", "10", "300s"),
        ("sentinel-scraping-service", "1Gi", "1", "5", "300s"),
        ("sentinel-ai-service", "512Mi", "1", "10", "300s")
    ]
    
    for service, memory, cpu, max_instances, timeout in services_config:
        optimize_service(service, memory, cpu, max_instances, timeout)
        print()
    
    print("✅ Optimization commands prepared")
    print("Run the commands above to apply optimizations")
 
if __name__ == "__main__":
    optimize_all_services()
