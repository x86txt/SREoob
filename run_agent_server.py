#!/usr/bin/env python3
"""
SiteUp Agent Server Runner
Runs the dedicated agent communication server on port 5227
"""

import os
import sys
import subprocess

def main():
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    print("Starting SiteUp Agent Server on port 5227...")
    print("This server handles agent registration and communication.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        # Run the agent server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.agent_server:agent_app",
            "--host", "0.0.0.0",
            "--port", "5227",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nAgent server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error running agent server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 