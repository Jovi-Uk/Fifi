
"""
Mannequin model for database integration and business logic.
Complete implementation with timer analytics support.
Fixed imports to work properly within the app structure.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class UserMeasurements:
    """User measurement data structure."""
    height_cm: float
    weight_kg: float
    gender: str  # 'male' or 'female'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'height_cm': self.height_cm,
            'weight_kg': self.weight_kg,
            'gender': self.gender
        }
    
    def validate(self) -> bool:
        """Validate measurement ranges"""
        if not (120 <= self.height_cm <= 220):
            return False
        if not (30 <= self.weight_kg <= 200):
            return False
        if self.gender not in ['male', 'female']:
            return False
        return True
    
    def calculate_bmi(self) -> float:
        """Calculate BMI from measurements"""
        height_m = self.height_cm / 100
        return self.weight_kg / (height_m ** 2)

@dataclass  
class MannequinResult:
    """Result from mannequin selection."""
    mannequin_id: int
    filename: str
    gender: str
    similarity_score: float
    estimated_height: float
    estimated_weight: float
    estimated_bmi: float
    file_path: str
    photo_enhanced: bool = False
    analysis_confidence: float = 0.0
    timer_enhanced: bool = False
    timer_effectiveness: Optional[float] = None
    
    @classmethod
    def from_selection_result(cls, result: Dict[str, Any]) -> 'MannequinResult':
        """Create MannequinResult from selection algorithm output."""
        return cls(
            mannequin_id=result['id'],
            filename=result['filename'],
            gender=result['gender'],
            similarity_score=result.get('similarity_score', 0.0),
            estimated_height=result['height_cm'],
            estimated_weight=result['weight_kg'],
            estimated_bmi=result['bmi'],
            file_path=f"/static/mannequins/{result['filename']}",
            photo_enhanced=result.get('photo_enhanced', False),
            analysis_confidence=result.get('analysis_confidence', 0.0),
            timer_enhanced=result.get('timer_enhanced', False),
            timer_effectiveness=result.get('timer_effectiveness')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'mannequin_id': self.mannequin_id,
            'filename': self.filename,
            'gender': self.gender,
            'similarity_score': self.similarity_score,
            'estimated_height': self.estimated_height,
            'estimated_weight': self.estimated_weight,
            'estimated_bmi': self.estimated_bmi,
            'file_path': self.file_path,
            'photo_enhanced': self.photo_enhanced,
            'analysis_confidence': self.analysis_confidence,
            'timer_enhanced': self.timer_enhanced,
            'timer_effectiveness': self.timer_effectiveness
        }

class MannequinService:
    """Service class for mannequin-related business logic."""
    
    def __init__(self, model_path: str = None, output_dir: str = None):
        """
        Initialize the mannequin service.
        
        Args:
            model_path: Path to SMPL models (defaults to app/models/smpl)
            output_dir: Path to mannequin output (defaults to static/mannequins)
        """

        if model_path is None:
            from flask import current_app
            if current_app:
                self.model_path = Path(current_app.root_path) / 'models' / 'smpl'
            else:
                self.model_path = Path('./app/models/smpl')
        else:
            self.model_path = Path(model_path)
            
        if output_dir is None:
            self.output_dir = Path('./static/mannequins')
        else:
            self.output_dir = Path(output_dir)
    
    def select_mannequin(self, measurements: UserMeasurements) -> Optional[MannequinResult]:
        """
        Select the best fitting mannequin for given user measurements.
        
        Args:
            measurements: User measurement data
            
        Returns:
            MannequinResult object or None if selection fails
        """
        try:

            if not measurements.validate():
                logger.warning(f"Invalid measurements: {measurements}")
                return None

            from app.services import get_mannequin_for_user
            
            result = get_mannequin_for_user(
                height_cm=measurements.height_cm,
                weight_kg=measurements.weight_kg,
                gender=measurements.gender,
                model_path=str(self.model_path),
                output_dir=str(self.output_dir)
            )
            
            if result:
                return MannequinResult.from_selection_result(result)
            else:
                logger.warning(f"No mannequin found for measurements: {measurements}")
                return None
                
        except Exception as e:
            logger.error(f"Error selecting mannequin: {e}")
            return None
    
    def get_mannequin_metadata(self, mannequin_id: int, gender: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific mannequin
        
        Args:
            mannequin_id: ID of the mannequin
            gender: Gender of the mannequin
            
        Returns:
            Mannequin metadata dictionary or None
        """
        try:

            from app.services import SMPLMannequinGenerator
            
            generator = SMPLMannequinGenerator(str(self.model_path), str(self.output_dir))
            generator.load_metadata()
            
            if gender in generator.mannequin_metadata:
                for mannequin in generator.mannequin_metadata[gender]:
                    if mannequin['id'] == mannequin_id:
                        return mannequin
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting mannequin metadata: {e}")
            return None
    
    def list_available_mannequins(self, gender: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all available mannequins
        
        Args:
            gender: Filter by gender ('male', 'female'), or None for all
            
        Returns:
            Dictionary with mannequin listings
        """
        try:

            from app.services import SMPLMannequinGenerator
            
            generator = SMPLMannequinGenerator(str(self.model_path), str(self.output_dir))
            generator.load_metadata()
            
            if gender:
                if gender in generator.mannequin_metadata:
                    return {gender: generator.mannequin_metadata[gender]}
                else:
                    return {gender: []}
            else:
                return generator.mannequin_metadata
                
        except Exception as e:
            logger.error(f"Error listing mannequins: {e}")
            return {'male': [], 'female': []}
    
    def get_mannequin_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available mannequins
        
        Returns:
            Dictionary with mannequin statistics
        """
        try:
            listings = self.list_available_mannequins()
            
            stats = {
                'total_mannequins': 0,
                'male_count': len(listings.get('male', [])),
                'female_count': len(listings.get('female', [])),
                'height_range': {'min': float('inf'), 'max': 0},
                'weight_range': {'min': float('inf'), 'max': 0},
                'bmi_range': {'min': float('inf'), 'max': 0}
            }
            
            stats['total_mannequins'] = stats['male_count'] + stats['female_count']

            for gender_mannequins in listings.values():
                for mannequin in gender_mannequins:
                    height = mannequin.get('height_cm', 0)
                    weight = mannequin.get('weight_kg', 0)
                    bmi = mannequin.get('bmi', 0)
                    
                    if height > 0:
                        stats['height_range']['min'] = min(stats['height_range']['min'], height)
                        stats['height_range']['max'] = max(stats['height_range']['max'], height)
                    if weight > 0:
                        stats['weight_range']['min'] = min(stats['weight_range']['min'], weight)
                        stats['weight_range']['max'] = max(stats['weight_range']['max'], weight)
                    if bmi > 0:
                        stats['bmi_range']['min'] = min(stats['bmi_range']['min'], bmi)
                        stats['bmi_range']['max'] = max(stats['bmi_range']['max'], bmi)

            if stats['total_mannequins'] == 0:
                stats['height_range'] = {'min': 0, 'max': 0}
                stats['weight_range'] = {'min': 0, 'max': 0}
                stats['bmi_range'] = {'min': 0, 'max': 0}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting mannequin statistics: {e}")
            return {
                'total_mannequins': 0,
                'male_count': 0,
                'female_count': 0,
                'height_range': {'min': 0, 'max': 0},
                'weight_range': {'min': 0, 'max': 0},
                'bmi_range': {'min': 0, 'max': 0}
            }
    
    def check_mannequin_availability(self) -> Dict[str, Any]:
        """
        Check if mannequins are properly generated and available
        
        Returns:
            Dictionary with availability status
        """
        try:
            metadata_file = self.output_dir / 'mannequin_metadata.json'
            
            if not metadata_file.exists():
                return {
                    'available': False,
                    'message': 'Mannequin metadata file not found. Please generate mannequins first.',
                    'metadata_path': str(metadata_file)
                }
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            male_count = len(metadata.get('male', []))
            female_count = len(metadata.get('female', []))
            total_count = male_count + female_count
            
            if total_count == 0:
                return {
                    'available': False,
                    'message': 'No mannequins found in metadata. Please generate mannequins.',
                    'metadata_path': str(metadata_file)
                }

            missing_files = []
            for gender in ['male', 'female']:
                for mannequin in metadata.get(gender, []):
                    file_path = self.output_dir / mannequin['filename']
                    if not file_path.exists():
                        missing_files.append(mannequin['filename'])
            
            if missing_files:
                return {
                    'available': False,
                    'message': f'Some mannequin files are missing: {", ".join(missing_files[:5])}...',
                    'missing_count': len(missing_files),
                    'total_count': total_count
                }
            
            return {
                'available': True,
                'message': 'All mannequins are available',
                'male_count': male_count,
                'female_count': female_count,
                'total_count': total_count,
                'metadata_path': str(metadata_file)
            }
            
        except Exception as e:
            logger.error(f"Error checking mannequin availability: {e}")
            return {
                'available': False,
                'message': f'Error checking mannequins: {str(e)}',
                'error': str(e)
            }

def get_mannequin_service() -> MannequinService:
    """Get a configured MannequinService instance"""
    return MannequinService()