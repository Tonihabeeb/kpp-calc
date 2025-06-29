#!/usr/bin/env python3
"""
Quick Test Script for KPP Simulation
Fast diagnostic check of current simulation status
"""

import json
import sys
import time

import requests


def quick_test():
    """Perform a quick diagnostic test"""
    base_url = "http://localhost:5000"

    print("KPP Simulation Quick Test")
    print("=" * 40)

    try:
        # Stop and restart simulation
        print("1. Stopping existing simulation...")
        requests.post(f"{base_url}/stop", headers={"Content-Type": "application/json"})
        time.sleep(1)

        print("2. Starting simulation...")
        response = requests.post(
            f"{base_url}/start",
            headers={"Content-Type": "application/json"},
            data=json.dumps({}),
        )

        if response.status_code != 200:
            print(f"   ✗ Failed to start: {response.status_code} - {response.text}")
            return False

        print("   ✓ Simulation started")

        print("3. Waiting for stabilization...")
        time.sleep(5)

        print("4. Checking results...")

        # Get summary data
        summary_response = requests.get(f"{base_url}/data/summary")
        summary = summary_response.json() if summary_response.status_code == 200 else {}

        # Get electrical data
        electrical_response = requests.get(f"{base_url}/data/electrical_status")
        electrical = (
            electrical_response.json() if electrical_response.status_code == 200 else {}
        )

        # Check CSV file
        csv_power = "N/A"
        try:
            with open("realtime_log.csv", "r") as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_line = lines[-1].strip().split(",")
                    if len(last_line) >= 2:
                        csv_power = f"{float(last_line[1]):.1f}W"
        except:
            pass

        # Print results
        power = summary.get("power", 0.0)
        torque = summary.get("torque", 0.0)
        efficiency = summary.get("overall_efficiency", 0.0)
        clutch = summary.get("clutch_engaged", False)

        gen_power = 0.0
        if electrical and "advanced_generator" in electrical:
            gen_power = electrical["advanced_generator"].get("electrical_power", 0.0)

        print(f"\nRESULTS:")
        print(f"   Summary Power:    {power:.1f} W")
        print(f"   Generator Power:  {gen_power:.1f} W")
        print(f"   CSV Power:        {csv_power}")
        print(f"   Torque:           {torque:.1f} N⋅m")
        print(f"   Efficiency:       {efficiency:.1%}")
        print(f"   Clutch Engaged:   {clutch}")

        # Diagnosis
        if power > 0:
            print(f"   STATUS: ✓ WORKING - Producing {power:.0f}W")
        elif gen_power > 0:
            print(
                f"   STATUS: ⚠ PARTIAL - Generator working ({gen_power:.0f}W) but main output is 0"
            )
        else:
            print(f"   STATUS: ✗ NOT WORKING - No power output")

        return power > 0

    except Exception as e:
        print(f"Error during test: {e}")
        return False


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
