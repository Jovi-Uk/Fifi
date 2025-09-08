#!/usr/bin/env python3
"""
SMPL Mannequin Generation and Selection Script

This script generates pre-computed 3D mannequins from SMPL models and provides
functionality to select the best fitting mannequin based on user characteristics.

Dependencies:
- torch
- smplx
- trimesh
- numpy
- scipy

Install with: pip install torch smplx trimesh numpy scipy
"""

import torch
import smplx
import trimesh
import numpy as np
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from flask import current_app
from scipy.spatial.distance import euclidean
import logging

logger = logging.getLogger(__name__)

class SMPLMannequinGenerator:
    """
    Handles SMPL model loading, mannequin generation, and user matching.
    """


    def __init__(self, model_path: str, output_dir: str):
        """
        Initialize the SMPL mannequin generator.
        """
        self.model_path = Path(model_path)
        self.output_dir = Path(output_dir)
    
        if not self.model_path.exists():
            raise FileNotFoundError(f"The model directory was not found at: {self.model_path}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.num_betas = 10
        self.num_mannequins = 70

        self.models = {}

        self.mannequin_metadata = {'male': [], 'female': []}
        
    def load_smpl_models(self) -> None:
        """Load SMPL models for male and female."""
        try:
            for gender in ['male', 'female']:
                logger.info(f"Loading SMPL {gender} model...")
                model = smplx.SMPL(
                    model_path=str(self.model_path),
                    gender=gender,
                    ext='pkl',
                    use_face_contour=False
                )
                self.models[gender] = model
                logger.info(f"Successfully loaded {gender} SMPL model")
                
        except Exception as e:
            logger.error(f"Error loading SMPL models: {e}")
            raise

    def generate_beta_variations(self) -> np.ndarray:
        """
        Generate beta parameter variations for diverse body shapes.
        
        The first few beta parameters control major body shape variations:
        - beta[0]: Overall body size/weight
        - beta[1]: Height variation  
        - beta[2]: Torso length
        - beta[3]: Upper body vs lower body proportion
        
        Returns:
            Array of shape (num_mannequins, num_betas) with beta variations
        """
        beta_variations = np.zeros((self.num_mannequins, self.num_betas))


        size_range = np.linspace(-2.5, 2.5, self.num_mannequins)
        
        for i, size_val in enumerate(size_range):

            beta_variations[i, 0] = size_val

            if i % 3 == 1:  # Every 3rd mannequin gets height variation
                beta_variations[i, 1] = np.random.normal(0, 0.5)
            if i % 4 == 2:  # Every 4th mannequin gets torso variation  
                beta_variations[i, 2] = np.random.normal(0, 0.3)
            if i % 5 == 3:  # Every 5th mannequin gets proportion variation
                beta_variations[i, 3] = np.random.normal(0, 0.3)
                
        return beta_variations

    def create_neutral_pose(self) -> torch.Tensor:
        """
        Create a neutral A-pose for the mannequin.
        
        Returns:
            Pose parameters tensor for A-pose
        """

        pose_params = torch.zeros(1, 72, dtype=torch.float32)
        
        return pose_params

    def generate_mannequin_mesh(self, gender: str, betas: np.ndarray) -> trimesh.Trimesh:
        """
        Generate a 3D mesh from SMPL model using given parameters.
        
        Args:
            gender: 'male' or 'female'
            betas: Shape parameters array
            
        Returns:
            Trimesh object of the generated mannequin
        """
        model = self.models[gender]

        betas_tensor = torch.tensor(betas, dtype=torch.float32).unsqueeze(0)
        pose_tensor = self.create_neutral_pose()

        with torch.no_grad():
            model_output = model(
                betas=betas_tensor,
                body_pose=pose_tensor[:, 3:],
                global_orient=pose_tensor[:, :3]
            )
            
        vertices = model_output.vertices.detach().cpu().numpy().squeeze()
        faces = model.faces

        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

        mesh.fix_normals()
        
        return mesh

    def calculate_physical_characteristics(self, mesh: trimesh.Trimesh, 
                                     betas: np.ndarray) -> Dict[str, float]:
         print("--- RUNNING THE NEW CORRECTED FUNCTION----")
         """
         Calculate approximate physical characteristics from the mesh.
         Args:
         mesh: Generated trimesh object
         betas: Beta parameters used to generate the mesh
         
         Returns:
         Dictionary with estimated height, weight, BMI
         """



         scaling_factor = 5.5
         mesh.apply_scale(scaling_factor)

         mesh.vertices[:, 2] -= mesh.bounds[0, 2]

         height_m = mesh.bounds[1, 2]
         
         height_cm = height_m * 100


         
         base_weight = 70.0  # Average weight in kg
         weight_variation = betas[0] * 15.0  # Each std dev ≈ 15kg variation
         estimated_weight = max(40.0, base_weight + weight_variation)

         bmi = estimated_weight / (height_m ** 2) if height_m > 0 else 22.0
         
         return {'height_cm': round(height_cm, 1),
                 'weight_kg': round(estimated_weight, 1),
                 'bmi': round(bmi, 1),
                 'primary_beta': round(betas[0], 2)
                 }

    def generate_all_mannequins(self) -> None:
        """Generate all mannequins for both genders and save metadata."""
        logger.info("Starting mannequin generation...")
        
        beta_variations = self.generate_beta_variations()
        batch_size = self.num_mannequins

        pose_tensor = self.create_neutral_pose()
        pose_batch = pose_tensor.expand(batch_size, -1)
        
        for gender in ['male', 'female']:
            logger.info(f"Generating batch of {batch_size} {gender} mannequins...")
            model = self.models[gender]
            betas_tensor = torch.tensor(beta_variations, dtype=torch.float32)
            gender_metadata = []
            
            try:

                with torch.no_grad():
                    model_output = model(betas=betas_tensor,
                                         body_pose=pose_batch[:, 3:],
                                         global_orient=pose_batch[:, :3],
                                         batch_size=batch_size)
                
                all_vertices = model_output.vertices.detach().cpu().numpy()
                faces = model.faces

                for i in range(batch_size):
                    mesh = trimesh.Trimesh(vertices=all_vertices[i], faces=faces)

                    characteristics = self.calculate_physical_characteristics(mesh, beta_variations[i])

                    filename = f'mannequin_{gender}_{i:02d}.glb'
                    filepath = self.output_dir / filename
                    mesh.export(str(filepath))

                    metadata = {
                        'id': i,
                        'filename': filename,
                        'gender': gender,
                        'betas': beta_variations[i].tolist(),
                        **characteristics
                    }
                    gender_metadata.append(metadata)

                    logger.info(f"Saved {filename}: H={characteristics['height_cm']}cm, "
                                f"W={characteristics['weight_kg']}kg, BMI={characteristics['bmi']}")
            except Exception as e:
                logger.error(f"Error during batch generation for {gender}: {e}", exc_info=True)
                continue

            self.mannequin_metadata[gender] = gender_metadata

            metadata_file = self.output_dir / 'mannequin_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(self.mannequin_metadata, f, indent=2)

            logger.info(f"Finished. Generated {len(self.mannequin_metadata.get('male', []))} male and "
                        f"{len(self.mannequin_metadata.get('female', []))} female mannequins.")
            logger.info(f"Metadata saved to {metadata_file}")

    def load_metadata(self) -> None:
        """Load existing mannequin metadata."""
        metadata_file = self.output_dir / 'mannequin_metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                self.mannequin_metadata = json.load(f)
        else:
            logger.warning("No metadata file found. Generate mannequins first.")

    def select_best_mannequin(self, user_height: float, user_weight: float, 
                            user_gender: str) -> Optional[Dict]:
        """
        Select the best fitting mannequin based on user characteristics.
        
        Args:
            user_height: User height in cm
            user_weight: User weight in kg  
            user_gender: 'male' or 'female'
            
        Returns:
            Dictionary with best matching mannequin metadata
        """
        if user_gender not in self.mannequin_metadata:
            logger.error(f"No mannequins available for gender: {user_gender}")
            return None
            
        if not self.mannequin_metadata[user_gender]:
            logger.error(f"No {user_gender} mannequins found in metadata")
            return None
        
        user_bmi = user_weight / ((user_height / 100) ** 2)
        
        best_match = None
        min_distance = float('inf')
        
        for mannequin in self.mannequin_metadata[user_gender]:

            height_diff = abs(mannequin['height_cm'] - user_height) / 10.0  # Scale by 10cm
            weight_diff = abs(mannequin['weight_kg'] - user_weight) / 5.0   # Scale by 5kg  
            bmi_diff = abs(mannequin['bmi'] - user_bmi) / 2.0               # Scale by 2 BMI units

            distance = np.sqrt(
                (height_diff * 1.5) ** 2 + 
                (weight_diff * 1.0) ** 2 + 
                (bmi_diff * 2.0) ** 2
            )
            
            if distance < min_distance:
                min_distance = distance
                best_match = mannequin.copy()
                best_match['similarity_score'] = round(max(0, 100 - distance * 10), 1)
        
        if best_match:
            logger.info(f"Selected mannequin {best_match['filename']} "
                       f"(similarity: {best_match['similarity_score']}%)")
        
        return best_match

def get_mannequin_for_user(height_cm: float, weight_kg: float, gender: str, 
                          model_path: str = './models/smpl', 
                          output_dir: str = './static/mannequins') -> Optional[Dict]:
    """
    Flask integration function to get best mannequin for user.
    
    Args:
        height_cm: User height in centimeters
        weight_kg: User weight in kilograms  
        gender: User gender ('male' or 'female')
        model_path: Path to SMPL models
        output_dir: Path to generated mannequins
        
    Returns:
        Dictionary with mannequin info or None if error
    """
    try:

        APP_ROOT = current_app.root_path

        MODELS_PATH = os.path.join(APP_ROOT, 'models', 'smpl')
        STATIC_MANNEQUINS_PATH = os.path.join(APP_ROOT, '..', 'static', 'mannequins')

        generator = SMPLMannequinGenerator(MODELS_PATH, STATIC_MANNEQUINS_PATH)
        generator.load_metadata()
        return generator.select_best_mannequin(height_cm, weight_kg, gender)
    except Exception as e:
        logger.error(f"Error selecting mannequin: {e}")
        return None

def initialize_mannequins(model_path: str,
                         output_dir: str) -> bool:
    """
    Initialize mannequins if they don't exist.
    
    Args:
        model_path: Path to SMPL models
        output_dir: Path to save mannequins
        
    Returns:
        True if successful, False otherwise
    """
    try:
        generator = SMPLMannequinGenerator(model_path, output_dir)

        metadata_file = Path(output_dir) / 'mannequin_metadata.json'
        if not metadata_file.exists():
            logger.info("No existing mannequins found. Generating...")
            generator.load_smpl_models()
            generator.generate_all_mannequins()
            
        return True
    except Exception as e:
        logger.error(f"Error initializing mannequins: {e}")
        return False
