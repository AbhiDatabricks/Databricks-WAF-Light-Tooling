#!/usr/bin/env python3
"""
Script to run install.ipynb notebook via Databricks CLI
Checks for errors and reports status
"""
import os
import json
import sys
import time
import subprocess
import requests

print("🔧 Running WAF Installation Notebook")
print("="*70)

# Get current user via CLI
try:
    result = subprocess.run(
        ['databricks', 'current-user', 'me'],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode == 0:
        user_data = json.loads(result.stdout)
        username = user_data.get('userName', 'unknown')
        print(f"👤 User: {username}")
    else:
        print(f"⚠️  Could not get current user: {result.stderr}")
        username = "unknown"
except Exception as e:
    print(f"⚠️  Error getting user: {e}")
    username = "unknown"

# Upload notebook to workspace
notebook_path = f"/Users/{username}/install"
local_notebook = "install.ipynb"

if not os.path.exists(local_notebook):
    print(f"❌ Error: {local_notebook} not found in current directory")
    sys.exit(1)

print(f"\n📤 Uploading notebook to {notebook_path}...")
try:
    result = subprocess.run(
        ['databricks', 'workspace', 'import', notebook_path, '--file', local_notebook, '--language', 'PYTHON', '--format', 'JUPYTER', '--overwrite'],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode == 0:
        print(f"✅ Notebook uploaded")
    else:
        print(f"❌ Error uploading notebook: {result.stderr}")
        if result.stdout:
            print(f"   stdout: {result.stdout}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error uploading notebook: {e}")
    sys.exit(1)

# Create and run job
job_name = f"WAF-Install-{int(time.time())}"
print(f"\n🚀 Creating job: {job_name}...")

job_config = {
    "name": job_name,
    "tasks": [{
        "task_key": "install",
        "notebook_task": {
            "notebook_path": notebook_path
        },
        "compute": [{
            "kind": "serverless"
        }]
    }]
}

try:
    result = subprocess.run(
        ['databricks', 'jobs', 'create', '--json', json.dumps(job_config)],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode == 0:
        job_data = json.loads(result.stdout)
        job_id = job_data.get('job_id')
        print(f"✅ Job created: {job_id}")
    else:
        print(f"❌ Error creating job: {result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error creating job: {e}")
    sys.exit(1)

# Run the job
print(f"\n▶️  Running job...")
try:
    result = subprocess.run(
        ['databricks', 'jobs', 'run-now', str(job_id), '--no-wait'],
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode == 0:
        run_data = json.loads(result.stdout)
        run_id = run_data.get('run_id')
        print(f"✅ Job run started: {run_id}")
    else:
        print(f"❌ Error starting job run: {result.stderr}")
        if result.stdout:
            print(f"   stdout: {result.stdout}")
        sys.exit(1)
except subprocess.TimeoutExpired:
    print(f"⚠️  Command timed out, but job may have started")
    print(f"   Check job status manually: databricks jobs list-runs --job-id {job_id} --limit 1")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting job run: {e}")
    sys.exit(1)

# Monitor job run
print(f"\n⏳ Monitoring job run (this may take a few minutes)...")
print(f"   (Press Ctrl+C to stop monitoring and check manually)")
max_wait = 600  # 10 minutes
start_time = time.time()
last_status = None

while True:
    try:
        result = subprocess.run(
            ['databricks', 'jobs', 'get-run', '--run-id', str(run_id)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            run_data = json.loads(result.stdout)
            state = run_data.get('state', {})
            current_status = state.get('life_cycle_state', 'UNKNOWN')
            
            if current_status != last_status:
                print(f"   Status: {current_status}")
                last_status = current_status
            
            if current_status in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
                result_state = state.get('result_state', 'UNKNOWN')
                
                print(f"\n{'='*70}")
                if result_state == "SUCCESS":
                    print("✅ JOB COMPLETED SUCCESSFULLY")
                else:
                    print(f"❌ JOB FAILED - Result: {result_state}")
                
                # Get run output
                try:
                    output_result = subprocess.run(
                        ['databricks', 'jobs', 'get-run-output', '--run-id', str(run_id)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if output_result.returncode == 0:
                        output_data = json.loads(output_result.stdout)
                        if output_data.get('error'):
                            print(f"\n❌ Error in notebook output:")
                            print(f"   {output_data['error']}")
                        if output_data.get('metadata'):
                            print(f"\n📊 Run metadata:")
                            print(f"   {json.dumps(output_data['metadata'], indent=2)}")
                except Exception as e:
                    print(f"⚠️  Could not get run output: {e}")
                
                break
        
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"\n⏰ Timeout after {max_wait} seconds")
            print(f"   Check job status manually: databricks jobs get-run --run-id {run_id}")
            break
        
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print(f"   Job run ID: {run_id}")
        print(f"   Check status: databricks jobs get-run --run-id {run_id}")
        break
    except Exception as e:
        print(f"\n❌ Error monitoring job: {e}")
        print(f"   Job run ID: {run_id}")
        print(f"   Check status: databricks jobs get-run --run-id {run_id}")
        break

print(f"\n{'='*70}")
print(f"📊 Job Details:")
print(f"   Job ID: {job_id}")
print(f"   Run ID: {run_id}")
print(f"\n💡 Next Steps:")
print(f"   1. Check the job run output above for any errors")
print(f"   2. Verify dashboard was created")
print(f"   3. Verify app was deployed")
print(f"   4. Check app URL if provided in output")
print(f"\n🔍 To check status manually:")
print(f"   databricks jobs get-run --run-id {run_id}")
print(f"   databricks jobs get-run-output --run-id {run_id}")
