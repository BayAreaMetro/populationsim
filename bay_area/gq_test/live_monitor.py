#!/usr/bin/env python3
"""
Live PopulationSim GQ Monitor
Checks for our fixed GQ expressions in real-time
"""

import time
import os
from datetime import datetime

def monitor_live():
    log_file = "output_2023/populationsim_working_dir/output/populationsim.log"
    print(f"🔍 MONITORING GQ EXPRESSIONS - Started at {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    print("Waiting for PopulationSim to process control expressions...")
    print("This should happen within the first 5-10 minutes.")
    print()
    
    checked_lines = 0
    found_expressions = False
    
    while not found_expressions:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Check new lines since last check
                new_lines = lines[checked_lines:]
                
                for line in new_lines:
                    line_strip = line.strip()
                    
                    # Look for our fixed expressions
                    if "gq_type == 1" in line:
                        print(f"✅ FOUND FIXED EXPRESSION: gq_type == 1")
                        print(f"   {line_strip}")
                        found_expressions = True
                    
                    elif "gq_type > 1" in line:
                        print(f"✅ FOUND FIXED EXPRESSION: gq_type > 1") 
                        print(f"   {line_strip}")
                        found_expressions = True
                    
                    # Look for old broken expressions
                    elif "hhgqtype==3" in line and "AGEP" in line:
                        print(f"❌ FOUND OLD EXPRESSION: hhgqtype with AGEP")
                        print(f"   {line_strip}")
                        print("❌ The controls.csv was not updated properly!")
                        return False
                    
                    # Look for POST-ASSIGNMENT results
                    elif "POST-ASSIGNMENT: gq_university has" in line:
                        print(f"📊 GQ University Assignment:")
                        print(f"   {line_strip}")
                        
                    elif "POST-ASSIGNMENT: gq_other has" in line:
                        print(f"📊 GQ Other Assignment:")
                        print(f"   {line_strip}")
                
                checked_lines = len(lines)
                
            except Exception as e:
                pass  # File might be locked, try again
        
        if not found_expressions:
            print(f"⏳ {datetime.now().strftime('%H:%M:%S')} - Still waiting for control processing...")
            time.sleep(30)  # Check every 30 seconds
    
    print()
    print("🎉 SUCCESS! Found our fixed GQ expressions!")
    print("✅ The fix is working - continue monitoring the run!")
    return True

if __name__ == "__main__":
    monitor_live()
