#!/usr/bin/env python3
"""
generate_mannequins.py - Developer/Admin tool for generating SMPL mannequins

This is a command-line utility for generating the 3D mannequin models
that are used by the Avatar Analyzer application. It should be run
once during setup or whenever you need to regenerate the mannequins.

Usage:
    python generate_mannequins.py                    # Generate all mannequins
    python generate_mannequins.py --count 50         # Generate 50 mannequins per gender
    python generate_mannequins.py --gender male      # Generate only male mannequins
    python generate_mannequins.py --check            # Check existing mannequins
    python generate_mannequins.py --clean            # Remove existing mannequins
"""

import argparse
import sys
import os
import json
import shutil
from pathlib import Path
import logging
from datetime import datetime
import time

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services import SMPLMannequinGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MannequinGeneratorCLI:
    """Command-line interface for mannequin generation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.model_path = self.project_root / 'app' / 'models' / 'smpl'
        self.output_dir = self.project_root / 'static' / 'mannequins'
        self.generator = None
        
    def check_smpl_models(self):
        """Check if SMPL model files are available"""
        logger.info("Checking for SMPL model files...")
        
        if not self.model_path.exists():
            logger.error(f"SMPL model directory not found: {self.model_path}")
            print("\n" + "="*60)
            print("ERROR: SMPL models not found!")
            print(f"Expected location: {self.model_path}")
            print("\nTo fix this:")
            print("1. Download SMPL models from https://smpl.is.tue.mpg.de/")
            print("2. Extract the models to the above directory")
            print("3. Ensure you have the .pkl files for male and female models")
            print("="*60 + "\n")
            return False

        required_files = ['SMPL_MALE.pkl', 'SMPL_FEMALE.pkl']
        missing_files = []
        
        for file in required_files:
            file_path = self.model_path / file
            if not file_path.exists():

                file_lower = self.model_path / file.lower()
                if not file_lower.exists():
                    missing_files.append(file)
                    
        if missing_files:
            logger.error(f"Missing SMPL model files: {missing_files}")
            print("\n" + "="*60)
            print("ERROR: Some SMPL model files are missing!")
            print(f"Missing files: {', '.join(missing_files)}")
            print(f"Expected in: {self.model_path}")
            print("="*60 + "\n")
            return False
            
        logger.info("✓ SMPL model files found")
        return True
        
    def check_existing_mannequins(self):
        """Check and report on existing mannequins"""
        metadata_file = self.output_dir / 'mannequin_metadata.json'
        
        if not metadata_file.exists():
            logger.info("No existing mannequins found")
            return None
            
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            male_count = len(metadata.get('male', []))
            female_count = len(metadata.get('female', []))
            total = male_count + female_count
            
            logger.info(f"Found existing mannequins: {total} total ({male_count} male, {female_count} female)")

            missing_files = []
            for gender in ['male', 'female']:
                for mannequin in metadata.get(gender, []):
                    file_path = self.output_dir / mannequin['filename']
                    if not file_path.exists():
                        missing_files.append(mannequin['filename'])
                        
            if missing_files:
                logger.warning(f"Found {len(missing_files)} missing mannequin files")
                
            return {
                'total': total,
                'male': male_count,
                'female': female_count,
                'missing_files': len(missing_files),
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
            return None
            
    def clean_existing_mannequins(self):
        """Remove all existing mannequins"""
        if not self.output_dir.exists():
            logger.info("No mannequins directory to clean")
            return
            
        logger.info(f"Cleaning directory: {self.output_dir}")

        glb_files = list(self.output_dir.glob('*.glb'))
        metadata_file = self.output_dir / 'mannequin_metadata.json'
        
        logger.info(f"Found {len(glb_files)} GLB files to remove")

        response = input("\nAre you sure you want to delete all mannequins? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Cleaning cancelled")
            return

        for file in glb_files:
            file.unlink()
            logger.debug(f"Removed: {file.name}")
            
        if metadata_file.exists():
            metadata_file.unlink()
            logger.debug("Removed metadata file")
            
        logger.info("✓ Mannequins cleaned successfully")
        
    def generate_mannequins(self, count=70, gender=None):
        """Generate new mannequins"""
        logger.info(f"Starting mannequin generation...")
        logger.info(f"Count per gender: {count}")
        logger.info(f"Gender filter: {gender or 'both'}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.generator = SMPLMannequinGenerator(
                str(self.model_path),
                str(self.output_dir)
            )

            if count != 70:
                self.generator.num_mannequins = count
                
        except Exception as e:
            logger.error(f"Failed to initialize generator: {e}")
            return False

        try:
            logger.info("Loading SMPL models...")
            start_time = time.time()
            self.generator.load_smpl_models()
            load_time = time.time() - start_time
            logger.info(f"✓ Models loaded in {load_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Failed to load SMPL models: {e}")
            print("\nMake sure you have the SMPL model files (.pkl) in the correct location")
            return False

        try:
            logger.info("Generating mannequins...")
            print("\nThis may take several minutes depending on your hardware...")
            
            start_time = time.time()

            self.generator.generate_all_mannequins()
            
            generation_time = time.time() - start_time

            metadata_file = self.output_dir / 'mannequin_metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                male_count = len(metadata.get('male', []))
                female_count = len(metadata.get('female', []))
                total = male_count + female_count
                
                print("\n" + "="*60)
                print("✓ MANNEQUIN GENERATION COMPLETE!")
                print(f"  Total mannequins: {total}")
                print(f"  Male mannequins: {male_count}")
                print(f"  Female mannequins: {female_count}")
                print(f"  Generation time: {generation_time:.2f} seconds")
                print(f"  Output directory: {self.output_dir}")
                print("="*60 + "\n")
                
                return True
            else:
                logger.error("Metadata file not created")
                return False
                
        except Exception as e:
            logger.error(f"Failed during generation: {e}", exc_info=True)
            return False
            
    def show_statistics(self):
        """Show statistics about generated mannequins"""
        existing = self.check_existing_mannequins()
        
        if not existing:
            print("\nNo mannequins found. Run generation first.")
            return
            
        metadata = existing['metadata']
        
        print("\n" + "="*60)
        print("MANNEQUIN STATISTICS")
        print("="*60)
        print(f"Total mannequins: {existing['total']}")
        print(f"Male mannequins: {existing['male']}")
        print(f"Female mannequins: {existing['female']}")
        
        if existing['missing_files'] > 0:
            print(f"\n⚠️  Warning: {existing['missing_files']} mannequin files are missing!")

        for gender in ['male', 'female']:
            if gender in metadata and metadata[gender]:
                mannequins = metadata[gender]
                heights = [m['height_cm'] for m in mannequins]
                weights = [m['weight_kg'] for m in mannequins]
                bmis = [m['bmi'] for m in mannequins]
                
                print(f"\n{gender.capitalize()} mannequins:")
                print(f"  Height range: {min(heights):.1f} - {max(heights):.1f} cm")
                print(f"  Weight range: {min(weights):.1f} - {max(weights):.1f} kg")
                print(f"  BMI range: {min(bmis):.1f} - {max(bmis):.1f}")
                
        print("="*60 + "\n")

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description='Generate SMPL mannequins for Avatar Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_mannequins.py              # Generate default mannequins
  python generate_mannequins.py --count 50   # Generate 50 mannequins per gender
  python generate_mannequins.py --check      # Check existing mannequins
  python generate_mannequins.py --clean      # Remove all mannequins
  python generate_mannequins.py --stats      # Show mannequin statistics
        """
    )
    
    parser.add_argument(
        '--count', 
        type=int, 
        default=70,
        help='Number of mannequins to generate per gender (default: 70)'
    )
    
    parser.add_argument(
        '--gender',
        choices=['male', 'female'],
        help='Generate only for specific gender'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check existing mannequins'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Remove all existing mannequins'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics about generated mannequins'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Custom output directory for mannequins'
    )
    
    args = parser.parse_args()

    cli = MannequinGeneratorCLI()

    if args.output_dir:
        cli.output_dir = Path(args.output_dir)
        logger.info(f"Using custom output directory: {cli.output_dir}")

    try:
        if args.check:
            cli.check_existing_mannequins()
            cli.show_statistics()
            
        elif args.clean:
            cli.clean_existing_mannequins()
            
        elif args.stats:
            cli.show_statistics()
            
        else:

            if not cli.check_smpl_models():
                sys.exit(1)

            existing = cli.check_existing_mannequins()
            if existing and existing['total'] > 0:
                print(f"\n⚠️  Found {existing['total']} existing mannequins")
                response = input("Do you want to regenerate them? (yes/no): ")
                if response.lower() != 'yes':
                    print("Generation cancelled")
                    sys.exit(0)

            success = cli.generate_mannequins(count=args.count, gender=args.gender)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n\nGeneration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()