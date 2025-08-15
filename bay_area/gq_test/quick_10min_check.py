#!/usr/bin/env python3
"""
Quick 10-minute GQ check
Run this after PopulationSim has been running for ~10 minutes
"""

import os
from pathlib import Path

def quick_gq_check():
    log_file = Path("output_2023/populationsim_working_dir/output/populationsim.log")
    
    if not log_file.exists():
        print("❌ PopulationSim log not found - is it running?")
        return
    
    print("🔍 QUICK GQ CHECK (10-minute mark)")
    print("=" * 50)
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Look for our fixed expressions
        if "gq_type == 1" in content:
            print("✅ Found FIXED expression: gq_type == 1")
        elif "hhgqtype==3" in content:
            print("❌ Found OLD expression: hhgqtype==3")
            print("❌ Controls were not updated properly!")
        else:
            print("⏳ GQ expressions not processed yet - wait a bit more")
        
        # Look for assignment results
        if "POST-ASSIGNMENT: gq_university has" in content:
            lines = content.split('\n')
            for line in lines:
                if "POST-ASSIGNMENT: gq_university has" in line:
                    print(f"📊 {line.strip()}")
                    if " 0 NaN values" in line and not any(char.isdigit() and int(char) > 0 for char in line.split("has")[1].split("NaN")[0]):
                        print("❌ This suggests 0 matches - GQ allocation failed!")
                    else:
                        print("✅ Non-zero values suggest GQ allocation working!")
        
        if "POST-ASSIGNMENT: gq_other has" in content:
            lines = content.split('\n')
            for line in lines:
                if "POST-ASSIGNMENT: gq_other has" in line:
                    print(f"📊 {line.strip()}")
    
    except Exception as e:
        print(f"Error reading log: {e}")

if __name__ == "__main__":
    quick_gq_check()
