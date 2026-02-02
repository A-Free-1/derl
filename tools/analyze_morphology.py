"""Analyze and compare evolved robot morphologies.

This script analyzes the structural properties of evolved robots from the output directory.
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np


def parse_robot_xml(xml_path):
    """Parse XML and extract morphology statistics."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Count bodies, joints, motors, etc.
        stats = {
            'num_bodies': len(root.findall('.//body')),
            'num_joints': len(root.findall('.//joint')),
            'num_motors': len(root.findall('.//motor')),
            'num_geoms': len(root.findall('.//geom')),
            'num_sites': len(root.findall('.//site')),
        }
        
        # Calculate total mass
        total_mass = 0
        for body in root.findall('.//body'):
            for inertial in body.findall('.//inertial'):
                mass_elem = inertial.find('mass')
                if mass_elem is not None and 'mass' in mass_elem.attrib:
                    try:
                        total_mass += float(mass_elem.attrib['mass'])
                    except:
                        pass
        stats['total_mass'] = total_mass
        
        # Extract torso position (center of robot)
        torso = root.find(".//body[@name='torso']")
        if torso is not None:
            pos = torso.attrib.get('pos', '0 0 0')
            stats['torso_pos'] = pos
        
        # Size metrics
        xml_size_kb = os.path.getsize(xml_path) / 1024
        stats['xml_size_kb'] = xml_size_kb
        
        return stats
    
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return None


def analyze_population(output_dir, sample_size=None):
    """Analyze morphology statistics of the entire population."""
    
    xml_dir = os.path.join(output_dir, "xml")
    if not os.path.exists(xml_dir):
        print(f"ERROR: XML directory not found: {xml_dir}")
        return
    
    xml_files = sorted([f for f in os.listdir(xml_dir) if f.endswith(".xml")])
    
    if not xml_files:
        print("No robots found!")
        return
    
    # Sample robots if needed
    if sample_size and sample_size < len(xml_files):
        np.random.seed(42)
        selected_indices = np.random.choice(len(xml_files), sample_size, replace=False)
        xml_files = [xml_files[i] for i in selected_indices]
    
    print(f"\n{'='*80}")
    print(f"Analyzing {len(xml_files)} robot morphologies")
    print(f"{'='*80}\n")
    
    # Collect statistics
    all_stats = []
    
    for idx, xml_file in enumerate(xml_files):
        xml_path = os.path.join(xml_dir, xml_file)
        stats = parse_robot_xml(xml_path)
        
        if stats:
            stats['filename'] = xml_file
            all_stats.append(stats)
        
        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1}/{len(xml_files)} robots...")
    
    if not all_stats:
        print("No valid robots found!")
        return
    
    # Calculate statistics
    print(f"\n{'='*80}")
    print(f"Morphology Statistics (from {len(all_stats)} robots):")
    print(f"{'='*80}\n")
    
    for key in ['num_bodies', 'num_joints', 'num_motors', 'num_geoms', 'num_sites', 'total_mass', 'xml_size_kb']:
        values = [s[key] for s in all_stats]
        print(f"{key:15s}: min={np.min(values):8.2f}, max={np.max(values):8.2f}, mean={np.mean(values):8.2f}, std={np.std(values):8.2f}")
    
    # Show extreme cases
    print(f"\n{'='*80}")
    print(f"Extreme Cases:")
    print(f"{'='*80}\n")
    
    # Simplest robot
    simplest = min(all_stats, key=lambda s: s['num_bodies'])
    print(f"Simplest (fewest bodies):")
    print(f"  - {simplest['filename']}")
    print(f"  - Bodies: {simplest['num_bodies']}, Joints: {simplest['num_joints']}, Motors: {simplest['num_motors']}")
    
    # Most complex robot
    most_complex = max(all_stats, key=lambda s: s['num_bodies'])
    print(f"\nMost complex (most bodies):")
    print(f"  - {most_complex['filename']}")
    print(f"  - Bodies: {most_complex['num_bodies']}, Joints: {most_complex['num_joints']}, Motors: {most_complex['num_motors']}")
    
    # Lightest robot
    lightest = min(all_stats, key=lambda s: s['total_mass'])
    print(f"\nLightest robot:")
    print(f"  - {lightest['filename']}")
    print(f"  - Total mass: {lightest['total_mass']:.4f}")
    
    # Heaviest robot
    heaviest = max(all_stats, key=lambda s: s['total_mass'])
    print(f"\nHeaviest robot:")
    print(f"  - {heaviest['filename']}")
    print(f"  - Total mass: {heaviest['total_mass']:.4f}")
    
    # Distribution analysis
    print(f"\n{'='*80}")
    print(f"Distribution Analysis:")
    print(f"{'='*80}\n")
    
    # Group by number of bodies
    body_counts = defaultdict(list)
    for stat in all_stats:
        body_counts[stat['num_bodies']].append(stat)
    
    print(f"Distribution by number of bodies:")
    for num_bodies in sorted(body_counts.keys())[:10]:  # Show top 10
        count = len(body_counts[num_bodies])
        pct = 100 * count / len(all_stats)
        print(f"  {num_bodies:3d} bodies: {count:4d} robots ({pct:5.1f}%)")
    
    if len(body_counts) > 10:
        print(f"  ... and {len(body_counts) - 10} more body counts")
    
    # Export results
    output_file = os.path.join(output_dir, "morphology_analysis.json")
    analysis = {
        'total_robots': len(all_stats),
        'statistics': {
            key: {
                'min': float(np.min([s[key] for s in all_stats])),
                'max': float(np.max([s[key] for s in all_stats])),
                'mean': float(np.mean([s[key] for s in all_stats])),
                'std': float(np.std([s[key] for s in all_stats])),
            }
            for key in ['num_bodies', 'num_joints', 'num_motors', 'num_geoms', 'num_sites', 'total_mass', 'xml_size_kb']
        },
        'extreme_cases': {
            'simplest': {
                'filename': simplest['filename'],
                'num_bodies': int(simplest['num_bodies']),
            },
            'most_complex': {
                'filename': most_complex['filename'],
                'num_bodies': int(most_complex['num_bodies']),
            },
            'lightest': {
                'filename': lightest['filename'],
                'total_mass': float(lightest['total_mass']),
            },
            'heaviest': {
                'filename': heaviest['filename'],
                'total_mass': float(heaviest['total_mass']),
            },
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Analysis saved to: {output_file}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze evolved robot morphologies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all robots
  python tools/analyze_morphology.py --output output/lunar_jump
  
  # Analyze sample of 100 robots
  python tools/analyze_morphology.py --output output/lunar_jump --sample 100
        """
    )
    
    parser.add_argument("--output", type=str, default="./output/lunar_jump", help="Output directory")
    parser.add_argument("--sample", type=int, default=None, help="Sample size (default: all)")
    
    args = parser.parse_args()
    
    output_dir = os.path.abspath(args.output)
    if not os.path.exists(output_dir):
        print(f"ERROR: Output directory not found: {output_dir}")
        sys.exit(1)
    
    analyze_population(output_dir, sample_size=args.sample)


if __name__ == "__main__":
    main()
