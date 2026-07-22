#!/bin/bash
# High-performance broad-spectrum scanning dashboard

while true; do
    clear
    echo "======================================================================"
    echo "📊 SOCOPILOT LIVE ENTERPRISE PIPELINE REAL-TIME MONITORING TELEMETRY"
    echo "======================================================================"
    echo "TIMESTAMP: $(date +'%Y-%m-%d %H:%M:%S')"
    echo "----------------------------------------------------------------------"
    
    echo -e "STAGE COUNTERS:\n"
    printf "%-35s | %-15s | %-10s\n" "STAGE MODULE" "METRIC TYPE" "VALUE"
    printf "%-35s+%-15s+%-10s\n" "-----------------------------------" "---------------" "----------"
    
    # Senior Pattern: Use broad prefix scan to guarantee key capture
    redis-cli --scan --pattern "metrics:stage:*" | sort | while read -r key; do
        if [[ ! "$key" == *"latency"* ]]; then
            stage=$(echo "$key" | cut -d':' -f3)
            metric=$(echo "$key" | cut -d':' -f4)
            val=$(redis-cli get "$key")
            printf "%-35s | %-15s | %-10s\n" "$stage" "$metric" "$val"
        fi
    done

    echo "----------------------------------------------------------------------"
    echo -e "STAGE LATENCY PROFILES (P99 Mean Ms Window):\n"
    printf "%-35s | %-25s\n" "PIPELINE COMPONENT STAGE" "LATEST DURATIONS"
    printf "%-35s+%-25s\n" "-----------------------------------" "-------------------------"
    
    redis-cli --scan --pattern "metrics:stage:*:latency_ms" | sort | while read -r key; do
        stage=$(echo "$key" | cut -d':' -f3)
        latencies=$(redis-cli lrange "$key" 0 3 | tr '\n' ' ')
        printf "%-35s | %-25s\n" "$stage" "$latencies ms"
    done
    echo "======================================================================"
    echo "[*] Refreshing telemetry matrix automatically every 1s. Press Ctrl+C to terminate."
    sleep 1
done
