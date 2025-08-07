#!/usr/bin/env python3
"""
Launch PopulationSim TM2 execution
"""

import subprocess
import sys
import os

def main():
    # Change to bay_area directory
    os.chdir(r"c:\GitHub\populationsim\bay_area")
    
    print("Starting PopulationSim TM2 for 2023...")
    print(f"Working directory: {os.getcwd()}")
    
    # Run PopulationSim
    cmd = [
        r"C:/Users/MTCPB/AppData/Local/anaconda3/Scripts/conda.exe",
        "run", "-p", r"C:\Users\MTCPB\AppData\Local\anaconda3",
        "--no-capture-output", "python", "run_populationsim_tm2.py", "2023"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True, cwd=os.getcwd())
        return result.returncode
    except Exception as e:
        print(f"Error executing PopulationSim: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
