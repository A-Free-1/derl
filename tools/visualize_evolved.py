"""Script to visualize evolved robots from output directory.

This script loads and visualizes already-evolved robot morphologies from
the output/lunar_jump/xml/ directory without needing metadata files.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import torch

from derl.config import cfg
from derl.envs.env_viewer import EnvViewer
from derl.envs.morphology import SymmetricUnimal
from derl.envs.tasks.lunar_jump import LunarJumpTask


def get_xml_files(output_dir):
    """Get all XML morphology files from output directory."""
    xml_dir = os.path.join(output_dir, "xml")
    if not os.path.exists(xml_dir):
        print(f"ERROR: XML directory not found at {xml_dir}")
        return []
    
    xml_files = sorted([f for f in os.listdir(xml_dir) if f.endswith(".xml")])
    return xml_files


def get_model_file(unimal_id, output_dir):
    """Get the model file for a given unimal ID if it exists."""
    model_dir = os.path.join(output_dir, "models")
    model_file = os.path.join(model_dir, f"{unimal_id}.pt")
    
    if os.path.exists(model_file):
        return model_file
    return None


def get_unimal_init_file(unimal_id, output_dir):
    """Get the unimal_init file for a given unimal ID if it exists."""
    init_dir = os.path.join(output_dir, "unimal_init")
    init_file = os.path.join(init_dir, f"{unimal_id}.pkl")
    
    if os.path.exists(init_file):
        return init_file
    return None


def load_unimal(xml_file, output_dir):
    """Load a unimal from XML file."""
    unimal_id = Path(xml_file).stem
    xml_path = os.path.join(output_dir, "xml", xml_file)
    
    try:
        # Check if we have unimal_init and model files
        init_file = get_unimal_init_file(unimal_id, output_dir)
        model_file = get_model_file(unimal_id, output_dir)
        
        # Load the unimal
        unimal = SymmetricUnimal(
            name="unimal",
            xml=xml_path,
            init_file=init_file,  # None if doesn't exist, SymmetricUnimal handles this
        )
        
        return unimal, model_file
    except Exception as e:
        print(f"Error loading {xml_file}: {e}")
        return None, None


def visualize_robot(xml_file, output_dir, use_viewer=True, num_steps=500):
    """Load and visualize a single robot."""
    print(f"\n{'='*60}")
    print(f"Loading: {xml_file}")
    print(f"{'='*60}")
    
    unimal, model_file = load_unimal(xml_file, output_dir)
    if unimal is None:
        return False
    
    # Create environment
    env = LunarJumpTask(
        unimal=unimal,
        floor=None,
        device=torch.device("cpu"),
    )
    env.reset()
    
    print(f"Robot loaded successfully!")
    print(f"  - XML: {xml_file}")
    if model_file:
        print(f"  - Model weights found at: {model_file}")
    else:
        print(f"  - Model weights: NOT FOUND (will use random initialization)")
    
    # Get environment info
    obs_size = env.obs_size()
    action_size = env.action_size()
    print(f"  - Observation size: {obs_size}")
    print(f"  - Action size: {action_size}")
    
    if use_viewer:
        # Use interactive viewer
        print(f"\nStarting interactive viewer...")
        print(f"Controls:")
        print(f"  - Space: Play/Pause")
        print(f"  - Right Arrow: Step forward")
        print(f"  - ESC: Exit")
        print(f"  - Right click + drag: Rotate view")
        print(f"  - Scroll: Zoom")
        
        viewer = EnvViewer(env)
        viewer.run()
    else:
        # Run without viewer, just step through
        print(f"\nRunning {num_steps} steps of simulation...")
        for step in range(num_steps):
            # Random action for visualization
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            
            if done:
                print(f"Episode ended at step {step}")
                break
            
            if (step + 1) % 100 == 0:
                print(f"  Step {step + 1}/{num_steps}")
    
    return True


def list_robots(output_dir):
    """List all available robots."""
    xml_files = get_xml_files(output_dir)
    
    if not xml_files:
        print("No XML files found in output directory!")
        return
    
    print(f"\nFound {len(xml_files)} evolved robot morphologies:\n")
    print(f"{'#':<6} {'Morphology ID':<45} {'Model':<10} {'Init':<10}")
    print("-" * 75)
    
    for idx, xml_file in enumerate(xml_files[:50]):  # Show first 50
        unimal_id = Path(xml_file).stem
        has_model = "✓" if get_model_file(unimal_id, output_dir) else "✗"
        has_init = "✓" if get_unimal_init_file(unimal_id, output_dir) else "✗"
        print(f"{idx:<6} {xml_file:<45} {has_model:<10} {has_init:<10}")
    
    if len(xml_files) > 50:
        print(f"... and {len(xml_files) - 50} more robots")
    
    print(f"\nTotal: {len(xml_files)} robots")
    print(f"Robots with trained weights (models/): {sum(1 for f in xml_files if get_model_file(Path(f).stem, output_dir))}")
    print(f"Robots with init files (unimal_init/): {sum(1 for f in xml_files if get_unimal_init_file(Path(f).stem, output_dir))}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Visualize evolved robot morphologies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all robots
  python tools/visualize_evolved.py --output output/lunar_jump --list
  
  # Visualize first robot with viewer
  python tools/visualize_evolved.py --output output/lunar_jump --index 0
  
  # Visualize specific robot by name
  python tools/visualize_evolved.py --output output/lunar_jump --name "0-1329-29-19-34-25.xml"
  
  # Run without viewer (headless)
  python tools/visualize_evolved.py --output output/lunar_jump --index 0 --headless
        """
    )
    
    parser.add_argument(
        "--cfg",
        dest="cfg_file",
        help="Config file (optional, uses default if not provided)",
        type=str,
        default=None,
    )
    
    parser.add_argument(
        "--output",
        dest="output_dir",
        help="Output directory containing evolved robots",
        type=str,
        default="./output/lunar_jump",
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available robots",
    )
    
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="Index of robot to visualize (0-based)",
    )
    
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Exact name of XML file to visualize",
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without interactive viewer",
    )
    
    parser.add_argument(
        "--steps",
        type=int,
        default=500,
        help="Number of simulation steps to run (for headless mode)",
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Load config if provided
    if args.cfg_file:
        cfg.merge_from_file(args.cfg_file)
    
    output_dir = os.path.abspath(args.output_dir)
    
    if not os.path.exists(output_dir):
        print(f"ERROR: Output directory not found: {output_dir}")
        sys.exit(1)
    
    # List all robots if requested
    if args.list:
        list_robots(output_dir)
        return
    
    # Get list of XML files
    xml_files = get_xml_files(output_dir)
    
    if not xml_files:
        print("No XML files found!")
        list_robots(output_dir)
        return
    
    # Determine which robot to visualize
    if args.name:
        if args.name not in xml_files:
            print(f"ERROR: Robot '{args.name}' not found!")
            print("\nAvailable robots:")
            list_robots(output_dir)
            sys.exit(1)
        target_xml = args.name
    elif args.index is not None:
        if args.index < 0 or args.index >= len(xml_files):
            print(f"ERROR: Index {args.index} out of range [0, {len(xml_files)-1}]")
            sys.exit(1)
        target_xml = xml_files[args.index]
    else:
        # Default to first robot
        target_xml = xml_files[0]
        print(f"No robot specified, using first one: {target_xml}")
    
    # Visualize the robot
    success = visualize_robot(
        target_xml,
        output_dir,
        use_viewer=not args.headless,
        num_steps=args.steps,
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
