
"""
Image Analysis Module for Avatar Analyzer
Extracts body measurements and proportions from user photos
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import math
from PIL import Image
import io

logger = logging.getLogger(__name__)

@dataclass
class BodyMeasurements:
    """Extracted body measurements from photos"""
    shoulder_width_ratio: float  # Shoulder width relative to height
    waist_hip_ratio: float      # Waist to hip ratio
    torso_leg_ratio: float      # Torso to leg length ratio
    arm_length_ratio: float     # Arm length relative to height
    chest_width_ratio: float    # Chest width relative to height
    symmetry_score: float       # Body symmetry measure (0-1)
    pose_quality_scores: Dict[str, float]  # Quality scores for each pose
    confidence_score: float     # Overall confidence in measurements

class ImageAnalyzer:
    """
    Analyzes user photos to extract body measurements and proportions
    """
    
    def __init__(self):

        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.5
        )
        
    def analyze_photos(self, photos: Dict[str, np.ndarray], 
                      user_height: float, user_weight: float) -> BodyMeasurements:
        """
        Analyze all 4 photos and extract comprehensive body measurements
        
        Args:
            photos: Dictionary with pose names as keys and image arrays as values
            user_height: User's height in cm
            user_weight: User's weight in kg
            
        Returns:
            BodyMeasurements object with extracted measurements
        """
        try:
            measurements = {}
            pose_qualities = {}

            for pose_name, image in photos.items():
                pose_data = self._analyze_single_pose(image, pose_name)
                if pose_data:
                    measurements[pose_name] = pose_data
                    pose_qualities[pose_name] = pose_data.get('quality_score', 0.0)
                    logger.info(f"Successfully analyzed {pose_name} pose")
                else:
                    logger.warning(f"Failed to analyze {pose_name} pose")
                    pose_qualities[pose_name] = 0.0

            return self._calculate_body_measurements(
                measurements, pose_qualities, user_height, user_weight
            )
            
        except Exception as e:
            logger.error(f"Error in photo analysis: {e}")

            return self._get_default_measurements()
    
    def _analyze_single_pose(self, image: np.ndarray, pose_name: str) -> Optional[Dict]:
        """
        Analyze a single pose photo and extract landmarks
        
        Args:
            image: Input image as numpy array
            pose_name: Name of the pose (front, left, right, back)
            
        Returns:
            Dictionary with pose analysis results
        """
        try:

            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image

            results = self.pose.process(rgb_image)
            
            if not results.pose_landmarks:
                logger.warning(f"No pose detected in {pose_name} image")
                return None

            landmarks = results.pose_landmarks.landmark
            h, w = image.shape[:2]

            pose_points = {}
            for i, landmark in enumerate(landmarks):
                pose_points[i] = {
                    'x': landmark.x * w,
                    'y': landmark.y * h,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                }

            if pose_name == 'front':
                return self._analyze_front_pose(pose_points, w, h)
            elif pose_name in ['left', 'right']:
                return self._analyze_side_pose(pose_points, w, h, pose_name)
            elif pose_name == 'back':
                return self._analyze_back_pose(pose_points, w, h)
            
        except Exception as e:
            logger.error(f"Error analyzing {pose_name} pose: {e}")
            return None
    
    def _analyze_front_pose(self, landmarks: Dict, w: int, h: int) -> Dict:
        """Extract measurements from front-facing pose"""
        try:

            LEFT_SHOULDER = 11
            RIGHT_SHOULDER = 12
            LEFT_HIP = 23
            RIGHT_HIP = 24
            LEFT_WRIST = 15
            RIGHT_WRIST = 16
            NOSE = 0
            LEFT_ANKLE = 27
            RIGHT_ANKLE = 28

            left_shoulder = landmarks[LEFT_SHOULDER]
            right_shoulder = landmarks[RIGHT_SHOULDER]
            shoulder_width = abs(right_shoulder['x'] - left_shoulder['x'])

            left_hip = landmarks[LEFT_HIP]
            right_hip = landmarks[RIGHT_HIP]
            hip_width = abs(right_hip['x'] - left_hip['x'])

            torso_length = abs(
                (left_shoulder['y'] + right_shoulder['y']) / 2 - 
                (left_hip['y'] + right_hip['y']) / 2
            )

            nose = landmarks[NOSE]
            avg_ankle_y = (landmarks[LEFT_ANKLE]['y'] + landmarks[RIGHT_ANKLE]['y']) / 2
            total_height = avg_ankle_y - nose['y']

            left_wrist = landmarks[LEFT_WRIST]
            right_wrist = landmarks[RIGHT_WRIST]
            arm_span = abs(right_wrist['x'] - left_wrist['x'])

            quality_score = self._calculate_pose_quality(landmarks, 'front')
            
            return {
                'shoulder_width': shoulder_width,
                'hip_width': hip_width,
                'torso_length': torso_length,
                'total_height': total_height,
                'arm_span': arm_span,
                'shoulder_width_ratio': shoulder_width / total_height if total_height > 0 else 0,
                'hip_width_ratio': hip_width / total_height if total_height > 0 else 0,
                'waist_hip_ratio': shoulder_width / hip_width if hip_width > 0 else 1.0,
                'quality_score': quality_score
            }
            
        except Exception as e:
            logger.error(f"Error in front pose analysis: {e}")
            return {'quality_score': 0.0}
    
    def _analyze_side_pose(self, landmarks: Dict, w: int, h: int, side: str) -> Dict:
        """Extract measurements from side profile pose"""
        try:

            NOSE = 0
            LEFT_SHOULDER = 11
            RIGHT_SHOULDER = 12
            LEFT_HIP = 23
            RIGHT_HIP = 24
            LEFT_KNEE = 25
            RIGHT_KNEE = 26
            LEFT_ANKLE = 27
            RIGHT_ANKLE = 28

            if side == 'left':
                shoulder = landmarks[LEFT_SHOULDER]
                hip = landmarks[LEFT_HIP]
                knee = landmarks[LEFT_KNEE]
                ankle = landmarks[LEFT_ANKLE]
            else:  # right
                shoulder = landmarks[RIGHT_SHOULDER]
                hip = landmarks[RIGHT_HIP]
                knee = landmarks[RIGHT_KNEE]
                ankle = landmarks[RIGHT_ANKLE]

            nose = landmarks[NOSE]

            torso_length = abs(hip['y'] - nose['y'])

            leg_length = abs(ankle['y'] - hip['y'])

            total_height = abs(ankle['y'] - nose['y'])

            center_x = w / 2
            body_depth = abs(shoulder['x'] - center_x)

            torso_leg_ratio = torso_length / leg_length if leg_length > 0 else 1.0

            quality_score = self._calculate_pose_quality(landmarks, 'side')
            
            return {
                'torso_length': torso_length,
                'leg_length': leg_length,
                'total_height': total_height,
                'body_depth': body_depth,
                'torso_leg_ratio': torso_leg_ratio,
                'body_depth_ratio': body_depth / total_height if total_height > 0 else 0,
                'quality_score': quality_score
            }
            
        except Exception as e:
            logger.error(f"Error in side pose analysis: {e}")
            return {'quality_score': 0.0}
    
    def _analyze_back_pose(self, landmarks: Dict, w: int, h: int) -> Dict:
        """Extract measurements from back-facing pose"""
        try:

            LEFT_SHOULDER = 11
            RIGHT_SHOULDER = 12
            LEFT_HIP = 23
            RIGHT_HIP = 24

            left_shoulder = landmarks[LEFT_SHOULDER]
            right_shoulder = landmarks[RIGHT_SHOULDER]
            back_shoulder_width = abs(right_shoulder['x'] - left_shoulder['x'])
            
            left_hip = landmarks[LEFT_HIP]
            right_hip = landmarks[RIGHT_HIP]
            back_hip_width = abs(right_hip['x'] - left_hip['x'])

            quality_score = self._calculate_pose_quality(landmarks, 'back')
            
            return {
                'back_shoulder_width': back_shoulder_width,
                'back_hip_width': back_hip_width,
                'back_shoulder_hip_ratio': back_shoulder_width / back_hip_width if back_hip_width > 0 else 1.0,
                'quality_score': quality_score
            }
            
        except Exception as e:
            logger.error(f"Error in back pose analysis: {e}")
            return {'quality_score': 0.0}
    
    def _calculate_pose_quality(self, landmarks: Dict, pose_type: str) -> float:
        """
        Calculate quality score for a pose based on landmark visibility and alignment
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        try:

            key_landmarks = [0, 11, 12, 23, 24, 27, 28]  # nose, shoulders, hips, ankles
            
            visibility_scores = []
            for idx in key_landmarks:
                if idx in landmarks:
                    visibility_scores.append(landmarks[idx].get('visibility', 0.0))
                else:
                    visibility_scores.append(0.0)

            avg_visibility = np.mean(visibility_scores)

            if 11 in landmarks and 12 in landmarks:
                left_shoulder_y = landmarks[11]['y']
                right_shoulder_y = landmarks[12]['y']
                shoulder_alignment = 1.0 - min(abs(left_shoulder_y - right_shoulder_y) / 50.0, 1.0)
            else:
                shoulder_alignment = 0.5

            quality_score = (avg_visibility * 0.7 + shoulder_alignment * 0.3)
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error calculating pose quality: {e}")
            return 0.5
    
    def _calculate_body_measurements(self, measurements: Dict, pose_qualities: Dict,
                                   user_height: float, user_weight: float) -> BodyMeasurements:
        """
        Calculate comprehensive body measurements from all poses
        """
        try:

            front_data = measurements.get('front', {})
            left_data = measurements.get('left', {})
            right_data = measurements.get('right', {})
            back_data = measurements.get('back', {})

            shoulder_ratios = []
            if front_data.get('shoulder_width_ratio'):
                shoulder_ratios.append(front_data['shoulder_width_ratio'])
            if back_data.get('back_shoulder_width'):

                shoulder_ratios.append(0.25)  # Typical ratio
            
            shoulder_width_ratio = np.mean(shoulder_ratios) if shoulder_ratios else 0.25

            waist_hip_ratio = front_data.get('waist_hip_ratio', 0.8)

            torso_leg_ratios = []
            for side_data in [left_data, right_data]:
                if side_data.get('torso_leg_ratio'):
                    torso_leg_ratios.append(side_data['torso_leg_ratio'])
            
            torso_leg_ratio = np.mean(torso_leg_ratios) if torso_leg_ratios else 1.0

            arm_length_ratio = front_data.get('shoulder_width_ratio', 0.25) * 1.2

            chest_width_ratio = shoulder_width_ratio * 0.8

            symmetry_score = self._calculate_symmetry_score(left_data, right_data)

            confidence_score = np.mean(list(pose_qualities.values()))
            
            return BodyMeasurements(
                shoulder_width_ratio=shoulder_width_ratio,
                waist_hip_ratio=waist_hip_ratio,
                torso_leg_ratio=torso_leg_ratio,
                arm_length_ratio=arm_length_ratio,
                chest_width_ratio=chest_width_ratio,
                symmetry_score=symmetry_score,
                pose_quality_scores=pose_qualities,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating body measurements: {e}")
            return self._get_default_measurements()
    
    def _calculate_symmetry_score(self, left_data: Dict, right_data: Dict) -> float:
        """Calculate body symmetry score from left and right side views"""
        try:
            if not left_data or not right_data:
                return 0.5

            similarities = []

            left_ratio = left_data.get('torso_leg_ratio', 1.0)
            right_ratio = right_data.get('torso_leg_ratio', 1.0)
            if left_ratio > 0 and right_ratio > 0:
                similarity = 1.0 - abs(left_ratio - right_ratio) / max(left_ratio, right_ratio)
                similarities.append(similarity)

            left_depth = left_data.get('body_depth_ratio', 0.1)
            right_depth = right_data.get('body_depth_ratio', 0.1)
            if left_depth > 0 and right_depth > 0:
                similarity = 1.0 - abs(left_depth - right_depth) / max(left_depth, right_depth)
                similarities.append(similarity)
            
            return np.mean(similarities) if similarities else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating symmetry: {e}")
            return 0.5
    
    def _get_default_measurements(self) -> BodyMeasurements:
        """Return default measurements when analysis fails"""
        return BodyMeasurements(
            shoulder_width_ratio=0.25,
            waist_hip_ratio=0.8,
            torso_leg_ratio=1.0,
            arm_length_ratio=0.3,
            chest_width_ratio=0.2,
            symmetry_score=0.5,
            pose_quality_scores={'front': 0.0, 'left': 0.0, 'right': 0.0, 'back': 0.0},
            confidence_score=0.1
        )

class EnhancedMannequinSelector:
    """
    Enhanced mannequin selection using both measurements and photo analysis
    """
    
    def __init__(self, generator):
        self.generator = generator
        
    def select_best_mannequin(self, user_height: float, user_weight: float, 
                            user_gender: str, body_measurements: BodyMeasurements) -> Optional[Dict]:
        """
        Select best mannequin using enhanced algorithm with photo data
        
        Args:
            user_height: User height in cm
            user_weight: User weight in kg
            user_gender: 'male' or 'female'
            body_measurements: Extracted measurements from photos
            
        Returns:
            Dictionary with best matching mannequin metadata
        """
        try:
            if user_gender not in self.generator.mannequin_metadata:
                logger.error(f"No mannequins available for gender: {user_gender}")
                return None
            
            if not self.generator.mannequin_metadata[user_gender]:
                logger.error(f"No {user_gender} mannequins found in metadata")
                return None
            
            user_bmi = user_weight / ((user_height / 100) ** 2)
            
            best_match = None
            min_distance = float('inf')
            
            for mannequin in self.generator.mannequin_metadata[user_gender]:

                distance = self._calculate_enhanced_distance(
                    user_height, user_weight, user_bmi, body_measurements, mannequin
                )
                
                if distance < min_distance:
                    min_distance = distance
                    best_match = mannequin.copy()

                    confidence_weight = body_measurements.confidence_score
                    base_similarity = max(0, 100 - distance * 10)
                    enhanced_similarity = base_similarity * (0.7 + 0.3 * confidence_weight)
                    
                    best_match['similarity_score'] = round(enhanced_similarity, 1)
                    best_match['analysis_confidence'] = round(confidence_weight * 100, 1)
                    best_match['photo_enhanced'] = True
            
            if best_match:
                logger.info(f"Enhanced selection: {best_match['filename']} "
                           f"(similarity: {best_match['similarity_score']}%, "
                           f"confidence: {best_match['analysis_confidence']}%)")
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error in enhanced mannequin selection: {e}")

            return self.generator.select_best_mannequin(user_height, user_weight, user_gender)
    
    def _calculate_enhanced_distance(self, user_height: float, user_weight: float, 
                                   user_bmi: float, body_measurements: BodyMeasurements, 
                                   mannequin: Dict) -> float:
        """
        Calculate enhanced distance using both basic measurements and photo analysis
        """
        try:

            height_diff = abs(mannequin['height_cm'] - user_height) / 10.0
            weight_diff = abs(mannequin['weight_kg'] - user_weight) / 5.0
            bmi_diff = abs(mannequin['bmi'] - user_bmi) / 2.0
            
            basic_distance = np.sqrt(
                (height_diff * 1.5) ** 2 + 
                (weight_diff * 1.0) ** 2 + 
                (bmi_diff * 2.0) ** 2
            )

            photo_weight = body_measurements.confidence_score
            
            if photo_weight > 0.3:  # Only use photo data if confidence is reasonable

                beta_diff = self._calculate_beta_differences(body_measurements, mannequin)

                enhanced_distance = (
                    basic_distance * (1 - photo_weight * 0.5) + 
                    beta_diff * photo_weight * 0.5
                )
            else:
                enhanced_distance = basic_distance
            
            return enhanced_distance
            
        except Exception as e:
            logger.error(f"Error calculating enhanced distance: {e}")
            return basic_distance
    
    def _calculate_beta_differences(self, body_measurements: BodyMeasurements, 
                                  mannequin: Dict) -> float:
        """
        Calculate differences based on SMPL beta parameters inferred from photos
        """
        try:


            expected_beta_0 = (body_measurements.shoulder_width_ratio - 0.25) * 4.0

            expected_beta_1 = (body_measurements.torso_leg_ratio - 1.0) * 2.0

            expected_beta_2 = (0.8 - body_measurements.waist_hip_ratio) * 3.0

            mannequin_betas = mannequin.get('betas', [0] * 10)
            mannequin_beta_0 = mannequin_betas[0] if len(mannequin_betas) > 0 else 0
            mannequin_beta_1 = mannequin_betas[1] if len(mannequin_betas) > 1 else 0
            mannequin_beta_2 = mannequin_betas[2] if len(mannequin_betas) > 2 else 0

            beta_0_diff = abs(expected_beta_0 - mannequin_beta_0)
            beta_1_diff = abs(expected_beta_1 - mannequin_beta_1)
            beta_2_diff = abs(expected_beta_2 - mannequin_beta_2)

            beta_distance = np.sqrt(
                (beta_0_diff * 2.0) ** 2 +
                (beta_1_diff * 1.0) ** 2 +
                (beta_2_diff * 1.5) ** 2
            )
            
            return beta_distance
            
        except Exception as e:
            logger.error(f"Error calculating beta differences: {e}")
            return 0.0

def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """Load image from bytes data"""
    try:

        pil_image = Image.open(io.BytesIO(image_bytes))

        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        image_array = np.array(pil_image)
        
        return image_array
        
    except Exception as e:
        logger.error(f"Error loading image from bytes: {e}")
        raise

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Preprocess image for better analysis"""
    try:

        h, w = image.shape[:2]
        max_size = 1024
        
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h))

        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(l)
        enhanced = cv2.merge([l, a, b])
        image = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        return image
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return image