#!/usr/bin/env python3
"""
Analyze PIR sensor data for baseline noise or movement patterns.

This script reads captured sensor data and generates visualizations to help
understand sensor behavior in different scenarios:
- Baseline mode: Analyze false positives when room is empty
- Movement mode: Analyze sensor coverage and trigger patterns during activity

Usage:
    uv run analyzeSensors.py <sensor_data.csv> [--movement]

    --movement: Analyze movement patterns instead of baseline noise

Output:
    - Console report with statistics
    - PNG plot showing patterns
"""

import sys
import csv
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def parse_timestamp(ts_str):
    """Parse timestamp string to datetime object."""
    return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S.%f')


def analyze_sensor_data(filename):
    """Read and analyze sensor data."""

    # Data structures for analysis
    sensor_stats = defaultdict(lambda: {
        'total_messages': 0,
        'trigger_count': 0,  # Count of 1s
        'quiet_count': 0,    # Count of 0s
        'name': '',
        'timestamps': [],
        'values': []
    })

    first_timestamp = None
    last_timestamp = None
    total_messages = 0

    print(f"Reading data from {filename}...")

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            timestamp = parse_timestamp(row['timestamp'])
            device_id = row['device_id']
            device_name = row['device_name']
            sensor_value = int(row['sensor_value'])

            # Track overall time range
            if first_timestamp is None:
                first_timestamp = timestamp
            last_timestamp = timestamp

            # Update sensor statistics
            stats = sensor_stats[device_id]
            stats['name'] = device_name
            stats['total_messages'] += 1
            stats['timestamps'].append(timestamp)
            stats['values'].append(sensor_value)

            if sensor_value == 1:
                stats['trigger_count'] += 1
            else:
                stats['quiet_count'] += 1

            total_messages += 1

    duration = (last_timestamp - first_timestamp).total_seconds()

    return sensor_stats, first_timestamp, last_timestamp, duration, total_messages


def print_baseline_report(sensor_stats, first_timestamp, last_timestamp, duration, total_messages):
    """Print console report of baseline noise statistics."""

    print("\n" + "=" * 80)
    print("BASELINE NOISE ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nCapture Period:")
    print(f"  Start:    {first_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"  End:      {last_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"  Total messages: {total_messages}")
    print(f"  Message rate: {total_messages/duration:.1f} messages/second")

    print("\n" + "-" * 80)
    print("SENSOR NOISE LEVELS (sorted by trigger percentage)")
    print("-" * 80)
    print(f"{'Sensor':<25} {'Total':<8} {'Triggers':<10} {'Noise %':<10} {'Trig/min':<10}")
    print("-" * 80)

    # Sort sensors by trigger percentage (descending)
    sorted_sensors = sorted(
        sensor_stats.items(),
        key=lambda x: x[1]['trigger_count'] / x[1]['total_messages'] if x[1]['total_messages'] > 0 else 0,
        reverse=True
    )

    for device_id, stats in sorted_sensors:
        total = stats['total_messages']
        triggers = stats['trigger_count']
        trigger_pct = (triggers / total * 100) if total > 0 else 0
        triggers_per_min = (triggers / duration * 60) if duration > 0 else 0

        print(f"{stats['name']:<25} {total:<8} {triggers:<10} {trigger_pct:>8.2f}%  {triggers_per_min:>8.2f}")

    print("-" * 80)

    # Identify problematic sensors
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    high_noise_sensors = [
        (stats['name'], stats['trigger_count'] / stats['total_messages'] * 100)
        for device_id, stats in sensor_stats.items()
        if stats['total_messages'] > 0 and (stats['trigger_count'] / stats['total_messages']) > 0.05
    ]

    if high_noise_sensors:
        print("\nHigh Noise Sensors (>5% trigger rate):")
        for name, pct in sorted(high_noise_sensors, key=lambda x: x[1], reverse=True):
            print(f"  - {name}: {pct:.1f}% noise")
        print("\nConsider:")
        print("  - Adjusting sensitivity potentiometer")
        print("  - Changing sensor orientation")
        print("  - Moving away from heat sources or air vents")
        print("  - Checking for nearby moving objects (curtains, fans, etc.)")
    else:
        print("\nAll sensors showing good baseline behavior (<5% noise)!")

    print("\n")


def print_movement_report(sensor_stats, first_timestamp, last_timestamp, duration, total_messages):
    """Print console report of movement pattern statistics."""

    print("\n" + "=" * 80)
    print("MOVEMENT PATTERN ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nCapture Period:")
    print(f"  Start:    {first_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"  End:      {last_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"  Total messages: {total_messages}")
    print(f"  Message rate: {total_messages/duration:.1f} messages/second")

    print("\n" + "-" * 80)
    print("SENSOR COVERAGE (sorted by trigger count)")
    print("-" * 80)
    print(f"{'Sensor':<25} {'Total':<8} {'Triggers':<10} {'Active %':<10} {'Trig/min':<10}")
    print("-" * 80)

    # Sort sensors by trigger count (descending)
    sorted_sensors = sorted(
        sensor_stats.items(),
        key=lambda x: x[1]['trigger_count'],
        reverse=True
    )

    for device_id, stats in sorted_sensors:
        total = stats['total_messages']
        triggers = stats['trigger_count']
        trigger_pct = (triggers / total * 100) if total > 0 else 0
        triggers_per_min = (triggers / duration * 60) if duration > 0 else 0

        print(f"{stats['name']:<25} {total:<8} {triggers:<10} {trigger_pct:>8.2f}%  {triggers_per_min:>8.2f}")

    print("-" * 80)

    # Analyze trigger sequences
    print("\n" + "=" * 80)
    print("COVERAGE ANALYSIS")
    print("=" * 80)

    # Count sensors that triggered
    triggered_sensors = [
        stats['name'] for device_id, stats in sensor_stats.items()
        if stats['trigger_count'] > 0
    ]

    total_sensors = len(sensor_stats)
    triggered_count = len(triggered_sensors)
    coverage_pct = (triggered_count / total_sensors * 100) if total_sensors > 0 else 0

    print(f"\nSensors triggered: {triggered_count}/{total_sensors} ({coverage_pct:.1f}%)")

    if triggered_sensors:
        print(f"\nActive sensors:")
        for name in sorted(triggered_sensors):
            print(f"  - {name}")

    # Find sensors that never triggered
    silent_sensors = [
        stats['name'] for device_id, stats in sensor_stats.items()
        if stats['trigger_count'] == 0
    ]

    if silent_sensors:
        print(f"\nSensors with no triggers:")
        for name in sorted(silent_sensors):
            print(f"  - {name}")
        print("\nConsider:")
        print("  - Walking through areas covered by these sensors")
        print("  - Checking sensor orientation and coverage zones")
        print("  - Verifying sensors are working correctly")
    else:
        print("\nAll sensors triggered - excellent coverage!")

    # Find most and least active sensors
    if sorted_sensors:
        most_active = sorted_sensors[0][1]
        least_active = sorted_sensors[-1][1]

        print(f"\nMost active sensor: {most_active['name']} ({most_active['trigger_count']} triggers)")
        print(f"Least active sensor: {least_active['name']} ({least_active['trigger_count']} triggers)")

    print("\n")


def create_movement_visualizations(sensor_stats, first_timestamp, last_timestamp, duration, input_filename):
    """Create movement pattern visualization plots."""

    print("Generating movement visualizations...")

    # Create figure with multiple subplots
    fig = plt.figure(figsize=(16, 12))

    # Sort sensors by name for consistent ordering
    sorted_sensors = sorted(sensor_stats.items(), key=lambda x: x[1]['name'])

    # --- Plot 1: Activity heatmap (trigger count) ---
    ax1 = plt.subplot(2, 2, 1)
    names = [stats['name'] for _, stats in sorted_sensors]
    trigger_counts = [stats['trigger_count'] for _, stats in sorted_sensors]

    colors = ['darkgreen' if cnt > 0 else 'lightgray' for cnt in trigger_counts]
    bars = ax1.barh(names, trigger_counts, color=colors, alpha=0.7)
    ax1.set_xlabel('Trigger Count')
    ax1.set_title('Sensor Activity Level\n(Green: Active, Gray: Inactive)')
    ax1.grid(axis='x', alpha=0.3)

    # --- Plot 2: Coverage percentage ---
    ax2 = plt.subplot(2, 2, 2)
    trigger_pcts = [
        (stats['trigger_count'] / stats['total_messages'] * 100) if stats['total_messages'] > 0 else 0
        for _, stats in sorted_sensors
    ]

    colors = ['steelblue' if pct > 0 else 'lightgray' for pct in trigger_pcts]
    ax2.barh(names, trigger_pcts, color=colors, alpha=0.7)
    ax2.set_xlabel('Active Time (%)')
    ax2.set_title('Percentage of Time Sensor Was Active')
    ax2.grid(axis='x', alpha=0.3)

    # --- Plot 3: Timeline of triggers ---
    ax3 = plt.subplot(2, 1, 2)

    # Plot each sensor's triggers over time
    has_any_triggers = False
    for idx, (device_id, stats) in enumerate(sorted_sensors):
        # Filter to only trigger events (value = 1)
        trigger_times = [ts for ts, val in zip(stats['timestamps'], stats['values']) if val == 1]
        trigger_values = [idx] * len(trigger_times)

        if trigger_times:
            ax3.scatter(trigger_times, trigger_values, alpha=0.6, s=30, label=stats['name'])
            has_any_triggers = True

    # Set x-axis limits to full timeline
    ax3.set_xlim(first_timestamp, last_timestamp)

    ax3.set_yticks(range(len(sorted_sensors)))
    ax3.set_yticklabels(names)
    ax3.set_xlabel('Time')

    if has_any_triggers:
        ax3.set_title('Movement Timeline (each dot = sensor trigger)')
    else:
        ax3.set_title('Movement Timeline (NO TRIGGERS DETECTED)')
        ax3.text(0.5, 0.5, 'No movement detected during capture period',
                ha='center', va='center', transform=ax3.transAxes,
                fontsize=12, style='italic', color='gray')

    ax3.grid(axis='x', alpha=0.3)

    # Format x-axis for time
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()

    # Save figure with name based on input file
    import os

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_filename = f'data/{base_name}_movement_analysis.png'
    plt.savefig(output_filename, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to: {output_filename}")

    return output_filename


def create_baseline_visualizations(sensor_stats, first_timestamp, last_timestamp, duration, input_filename):
    """Create baseline noise visualization plots."""

    print("Generating baseline visualizations...")

    # Create figure with multiple subplots
    fig = plt.figure(figsize=(16, 10))

    # Sort sensors by name for consistent ordering
    sorted_sensors = sorted(sensor_stats.items(), key=lambda x: x[1]['name'])

    # --- Plot 1: Trigger percentage bar chart ---
    ax1 = plt.subplot(2, 2, 1)
    names = [stats['name'] for _, stats in sorted_sensors]
    trigger_pcts = [
        (stats['trigger_count'] / stats['total_messages'] * 100) if stats['total_messages'] > 0 else 0
        for _, stats in sorted_sensors
    ]

    colors = ['red' if pct > 5 else 'orange' if pct > 1 else 'green' for pct in trigger_pcts]
    bars = ax1.barh(names, trigger_pcts, color=colors, alpha=0.7)
    ax1.set_xlabel('Trigger Percentage (%)')
    ax1.set_title('Baseline Noise Level by Sensor\n(Green: <1%, Orange: 1-5%, Red: >5%)')
    ax1.axvline(x=5, color='red', linestyle='--', linewidth=1, alpha=0.5, label='5% threshold')
    ax1.axvline(x=1, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='1% threshold')
    ax1.legend()
    ax1.grid(axis='x', alpha=0.3)

    # --- Plot 2: Total triggers bar chart ---
    ax2 = plt.subplot(2, 2, 2)
    total_triggers = [stats['trigger_count'] for _, stats in sorted_sensors]
    ax2.barh(names, total_triggers, color='steelblue', alpha=0.7)
    ax2.set_xlabel('Total Trigger Count')
    ax2.set_title('Total False Triggers (Absolute Count)')
    ax2.grid(axis='x', alpha=0.3)

    # --- Plot 3: Timeline of triggers ---
    ax3 = plt.subplot(2, 1, 2)

    # Plot each sensor's triggers over time
    has_any_triggers = False
    for idx, (device_id, stats) in enumerate(sorted_sensors):
        # Filter to only trigger events (value = 1)
        trigger_times = [ts for ts, val in zip(stats['timestamps'], stats['values']) if val == 1]
        trigger_values = [idx] * len(trigger_times)

        if trigger_times:
            ax3.scatter(trigger_times, trigger_values, alpha=0.6, s=20, label=stats['name'])
            has_any_triggers = True

    # Set x-axis limits to full timeline
    ax3.set_xlim(first_timestamp, last_timestamp)

    ax3.set_yticks(range(len(sorted_sensors)))
    ax3.set_yticklabels(names)
    ax3.set_xlabel('Time')

    if has_any_triggers:
        ax3.set_title('Timeline of Sensor Triggers (each dot = false positive)')
    else:
        ax3.set_title('Timeline of Sensor Triggers (NO TRIGGERS - EXCELLENT!)')
        ax3.text(0.5, 0.5, 'No false positives detected - perfect baseline!',
                ha='center', va='center', transform=ax3.transAxes,
                fontsize=12, style='italic', color='green')

    ax3.grid(axis='x', alpha=0.3)

    # Format x-axis for time
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()

    # Save figure with name based on input file
    import os

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_filename = f'data/{base_name}_analysis.png'
    plt.savefig(output_filename, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to: {output_filename}")

    return output_filename


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run analyzeSensors.py <sensor_data.csv> [--movement]")
        print("\nExamples:")
        print("  uv run analyzeSensors.py data/sensor_data_20251021_221902.csv")
        print("  uv run analyzeSensors.py data/sensor_data_20251021_221902.csv --movement")
        sys.exit(1)

    # Parse arguments
    filename = sys.argv[1]
    movement_mode = '--movement' in sys.argv

    try:
        # Analyze the data
        sensor_stats, first_ts, last_ts, duration, total = analyze_sensor_data(filename)

        if movement_mode:
            # Movement pattern analysis
            print_movement_report(sensor_stats, first_ts, last_ts, duration, total)
            output_file = create_movement_visualizations(sensor_stats, first_ts, last_ts, duration, filename)
        else:
            # Baseline noise analysis
            print_baseline_report(sensor_stats, first_ts, last_ts, duration, total)
            output_file = create_baseline_visualizations(sensor_stats, first_ts, last_ts, duration, filename)

        print(f"\nAnalysis complete!")
        print(f"Review the plot: {output_file}")

    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
