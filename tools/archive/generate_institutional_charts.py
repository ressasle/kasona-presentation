#!/usr/bin/env python3
import matplotlib.pyplot as plt
import argparse
import os
from pathlib import Path

# Kasona Professional Color Palette
COLOR_KASONA_DARK = "#0f172a"
COLOR_KASONA_ORANGE = "#F36C21"
COLOR_PRIMARY_BLUE = "#1E3A8A"
COLOR_WHITE = "#FFFFFF"
COLOR_SLATE_600 = "#334155"
COLOR_LIGHT_BG = "#f8fafc"

CHART_COLORS = [COLOR_PRIMARY_BLUE, COLOR_KASONA_ORANGE, COLOR_SLATE_600, "#0ea5e9", "#6366f1", "#8b5cf6"]

def generate_pie_chart(labels, values, title, output_path):
    # Setup styling
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 7), facecolor=COLOR_KASONA_DARK)
    ax.set_facecolor(COLOR_KASONA_DARK)
    
    # Generate Pie
    wedges, texts, autotexts = ax.pie(
        values, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=CHART_COLORS,
        textprops={'color': COLOR_WHITE, 'fontsize': 14, 'fontweight': 'bold'},
        pctdistance=0.85,
        explode=[0.05] * len(labels) # Subtle separation
    )
    
    # Add a hole in the middle (Donut Chart looks more institutional)
    centre_circle = plt.Circle((0,0), 0.70, fc=COLOR_KASONA_DARK)
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    
    plt.title(title, color=COLOR_WHITE, fontsize=18, fontweight='bold', pad=20)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=False)
    plt.close()
    print(f"[OK] Chart generated: {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True, help="Comma-separated labels")
    parser.add_argument("--values", required=True, help="Comma-separated values")
    parser.add_argument("--title", default="Revenue Breakdown")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    labels = [l.strip() for l in args.labels.split(",")]
    values = [float(v.strip()) for v in args.values.split(",")]
    
    generate_pie_chart(labels, values, args.title, args.output)

if __name__ == "__main__":
    main()
