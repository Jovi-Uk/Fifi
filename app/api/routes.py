
"""
Complete API routes for Avatar Analyzer with timer integration
Fixed endpoint names to match frontend expectations
"""

from flask import Blueprint, request, jsonify, current_app, session
import logging
import json
import os
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime
import numpy as np

from app.services import get_mannequin_for_user, SMPLMannequinGenerator
from app.analytics import AnalyticsManager, AnalysisSession

try:
    from app.image_analysis import (
        ImageAnalyzer, EnhancedMannequinSelector, 
        load_image_from_bytes, preprocess_image
    )
    ENHANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ENHANCED_ANALYSIS_AVAILABLE = False
    logging.warning("Enhanced image analysis not available")

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

analytics_manager = AnalyticsManager()

@api_bp.route('/analyze', methods=['POST'])
def generate_avatar():
    """
    Main API endpoint for basic avatar generation.
    This endpoint is called by the frontend form submission.
    
    Expected JSON data:
    {
        "height": float,
        "weight": float,
        "gender": string
    }
    """
    start_time = time.time()
    session_id = f'basic_{int(time.time())}'
    
    try:
        logger.info("Starting basic avatar generation")

        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()

        required_fields = ['height', 'weight', 'gender']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        try:
            height = float(data['height'])
            weight = float(data['weight'])
            gender = str(data['gender']).lower().strip()
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': f'Invalid measurement data: {str(e)}'
            }), 400

        if not (120 <= height <= 220):
            return jsonify({
                'success': False,
                'error': 'Height must be between 120cm and 220cm'
            }), 400
        if not (30 <= weight <= 200):
            return jsonify({
                'success': False,
                'error': 'Weight must be between 30kg and 200kg'
            }), 400
        if gender not in ['male', 'female']:
            return jsonify({
                'success': False,
                'error': 'Gender must be "male" or "female"'
            }), 400

        selection_start = time.time()
        try:
            mannequin_result = get_mannequin_for_user(height, weight, gender)
            
            if not mannequin_result:
                return jsonify({
                    'success': False,
                    'error': 'Unable to find suitable mannequin'
                }), 500
            
            selection_time = time.time() - selection_start
            logger.info(f"Basic mannequin selection completed in {selection_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in basic mannequin selection: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to select mannequin'
            }), 500

        bmi = weight / ((height / 100) ** 2)

        total_processing_time = time.time() - start_time
        response_data = {
            'success': True,
            'analysis_complete': True,
            'analysis_type': 'basic',
            'user_measurements': {
                'height_cm': height,
                'weight_kg': weight,
                'gender': gender,
                'bmi': round(bmi, 1)
            },
            'mannequin': {
                'mannequin_id': mannequin_result['id'],
                'filename': mannequin_result['filename'],
                'gender': mannequin_result['gender'],
                'similarity_score': mannequin_result.get('similarity_score', 0.0),
                'estimated_height': mannequin_result['height_cm'],
                'estimated_weight': mannequin_result['weight_kg'],
                'estimated_bmi': mannequin_result['bmi'],
                'file_path': f"/static/mannequins/{mannequin_result['filename']}",
                'photo_enhanced': False,
                'analysis_confidence': 100.0,
                'timer_enhanced': False
            },
            'similarity_score': mannequin_result.get('similarity_score', 0.0),
            'performance_metrics': {
                'total_processing_time': round(total_processing_time, 2),
                'selection_time': round(selection_time, 2)
            }
        }

        session['avatar_result'] = response_data

        try:
            analytics_session = AnalysisSession(
                session_id=session_id,
                timestamp=datetime.now(),
                user_height=height,
                user_weight=weight,
                user_gender=gender,
                analysis_type='basic',
                selected_mannequin_id=mannequin_result['id'],
                similarity_score=mannequin_result.get('similarity_score', 0.0),
                confidence_score=100.0,
                processing_time=total_processing_time,
                photo_count=0,
                pose_quality_scores={},
                user_agent=request.headers.get('User-Agent', 'Unknown'),
                ip_address=request.remote_addr or 'Unknown',
                completion_status='success'
            )
            
            analytics_manager.log_analysis_session(analytics_session)
        except Exception as e:
            logger.error(f"Failed to log analytics session: {e}")
        
        logger.info(f"Basic avatar generation complete for user: {gender}, {height}cm, {weight}kg. "
                   f"Selected: {mannequin_result['filename']} "
                   f"(similarity: {mannequin_result.get('similarity_score', 0):.1f}%)")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in generate-avatar endpoint: {e}", exc_info=True)

        try:
            analytics_session = AnalysisSession(
                session_id=session_id,
                timestamp=datetime.now(),
                user_height=data.get('height', 0),
                user_weight=data.get('weight', 0),
                user_gender=data.get('gender', 'unknown'),
                analysis_type='basic',
                selected_mannequin_id=0,
                similarity_score=0.0,
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                photo_count=0,
                pose_quality_scores={},
                user_agent=request.headers.get('User-Agent', 'Unknown'),
                ip_address=request.remote_addr or 'Unknown',
                completion_status='error'
            )
            analytics_manager.log_analysis_session(analytics_session)
        except:
            pass
            
        return jsonify({
            'success': False,
            'error': 'Internal server error during avatar generation'
        }), 500

@api_bp.route('/analyze-enhanced', methods=['POST'])
def analyze_user_enhanced():
    """
    Enhanced analysis endpoint with timer metadata processing
    
    Expected form data:
    - height: float
    - weight: float  
    - gender: string
    - analysis_type: 'enhanced'
    - photo_front: file
    - photo_left: file
    - photo_right: file
    - photo_back: file
    - photo_metadata: JSON string (includes timer data)
    """
    start_time = time.time()
    session_id = f'enhanced_{int(time.time())}'
    
    try:
        logger.info("Starting enhanced photo analysis with timer metadata")
        
        if not ENHANCED_ANALYSIS_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Enhanced analysis not available on this server'
            }), 503

        if 'height' not in request.form:
            return jsonify({'success': False, 'error': 'Missing height parameter'}), 400
        if 'weight' not in request.form:
            return jsonify({'success': False, 'error': 'Missing weight parameter'}), 400
        if 'gender' not in request.form:
            return jsonify({'success': False, 'error': 'Missing gender parameter'}), 400

        try:
            height = float(request.form['height'])
            weight = float(request.form['weight'])
            gender = str(request.form['gender']).lower().strip()
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'error': f'Invalid measurement data: {str(e)}'}), 400

        if not (120 <= height <= 220):
            return jsonify({'success': False, 'error': 'Height must be between 120cm and 220cm'}), 400
        if not (30 <= weight <= 200):
            return jsonify({'success': False, 'error': 'Weight must be between 30kg and 200kg'}), 400
        if gender not in ['male', 'female']:
            return jsonify({'success': False, 'error': 'Gender must be "male" or "female"'}), 400

        photo_metadata = {}
        timer_metadata = {}
        if 'photo_metadata' in request.form:
            try:
                photo_metadata = json.loads(request.form['photo_metadata'])
                timer_metadata = photo_metadata.get('timer_settings', {})
                logger.info(f"Photo metadata received: {len(photo_metadata)} keys")
            except json.JSONDecodeError:
                logger.warning("Invalid photo metadata JSON")

        required_poses = ['front', 'left', 'right', 'back']
        uploaded_photos = {}
        
        for pose in required_poses:
            file_key = f'photo_{pose}'
            if file_key not in request.files:
                return jsonify({'success': False, 'error': f'Missing {pose} photo'}), 400
            
            file = request.files[file_key]
            if file.filename == '':
                return jsonify({'success': False, 'error': f'Empty {pose} photo'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': f'Invalid file type for {pose} photo. Use JPG, JPEG, or PNG'}), 400
            
            if not validate_file_size(file):
                return jsonify({'success': False, 'error': f'{pose} photo is too large. Maximum size is 5MB'}), 400
            
            uploaded_photos[pose] = file
        
        logger.info(f"Received {len(uploaded_photos)} photos for timer-enhanced analysis")

        photo_processing_start = time.time()
        try:
            photo_arrays = {}
            
            for pose, file in uploaded_photos.items():

                file_data = file.read()
                file.seek(0)  # Reset for potential future reads

                image_array = load_image_from_bytes(file_data)
                processed_image = preprocess_image_with_timer_data(
                    image_array, 
                    timer_metadata.get('timers_used', [5]), 
                    pose
                )
                
                photo_arrays[pose] = processed_image
                logger.info(f"Successfully processed {pose} photo: {processed_image.shape}")
            
            photo_processing_time = time.time() - photo_processing_start
            logger.info(f"Photo processing completed in {photo_processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing photos: {e}")
            return jsonify({'success': False, 'error': 'Failed to process uploaded photos'}), 400

        analysis_start = time.time()
        try:
            analyzer = ImageAnalyzer()
            body_measurements = analyzer.analyze_photos_with_timer_context(
                photo_arrays, height, weight, timer_metadata
            )
            
            analysis_time = time.time() - analysis_start
            logger.info(f"Image analysis complete in {analysis_time:.2f}s. Confidence: {body_measurements.confidence_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            return jsonify({'success': False, 'error': 'Failed to analyze photos'}), 500

        selection_start = time.time()
        try:

            model_path = os.path.join(current_app.root_path, 'models', 'smpl')
            output_dir = os.path.join(current_app.root_path, '..', 'static', 'mannequins')
            
            generator = SMPLMannequinGenerator(model_path, output_dir)
            generator.load_metadata()

            enhanced_selector = EnhancedMannequinSelector(generator)
            mannequin_result = enhanced_selector.select_best_mannequin_with_timer_context(
                height, weight, gender, body_measurements, timer_metadata
            )
            
            if not mannequin_result:
                return jsonify({'success': False, 'error': 'Unable to find suitable mannequin'}), 500
            
            selection_time = time.time() - selection_start
            logger.info(f"Mannequin selection completed in {selection_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in enhanced mannequin selection: {e}")
            return jsonify({'success': False, 'error': 'Failed to select mannequin'}), 500

        timer_effectiveness = calculate_timer_effectiveness(timer_metadata, body_measurements)

        bmi = weight / ((height / 100) ** 2)

        total_processing_time = time.time() - start_time
        response_data = {
            'success': True,
            'analysis_complete': True,
            'analysis_type': 'enhanced_with_timer',
            'user_measurements': {
                'height_cm': height,
                'weight_kg': weight,
                'gender': gender,
                'bmi': round(bmi, 1)
            },
            'mannequin': {
                'mannequin_id': mannequin_result['id'],
                'filename': mannequin_result['filename'],
                'gender': mannequin_result['gender'],
                'similarity_score': mannequin_result.get('similarity_score', 0.0),
                'estimated_height': mannequin_result['height_cm'],
                'estimated_weight': mannequin_result['weight_kg'],
                'estimated_bmi': mannequin_result['bmi'],
                'file_path': f"/static/mannequins/{mannequin_result['filename']}",
                'photo_enhanced': mannequin_result.get('photo_enhanced', True),
                'analysis_confidence': mannequin_result.get('analysis_confidence', 0.0),
                'timer_enhanced': True
            },
            'similarity_score': mannequin_result.get('similarity_score', 0.0),
            'photo_analysis': {
                'confidence_score': round(body_measurements.confidence_score * 100, 1),
                'shoulder_width_ratio': round(body_measurements.shoulder_width_ratio, 3),
                'waist_hip_ratio': round(body_measurements.waist_hip_ratio, 3),
                'torso_leg_ratio': round(body_measurements.torso_leg_ratio, 3),
                'symmetry_score': round(body_measurements.symmetry_score * 100, 1),
                'pose_quality_scores': {
                    pose: round(score * 100, 1) 
                    for pose, score in body_measurements.pose_quality_scores.items()
                }
            },
            'timer_analytics': {
                'effectiveness_score': timer_effectiveness,
                'timer_usage': timer_metadata.get('timers_used', []),
                'average_timer': timer_metadata.get('average_timer', 5),
                'consistency': timer_metadata.get('timer_consistency', 'unknown'),
                'photo_quality_impact': assess_timer_quality_impact(timer_metadata, body_measurements),
                'recommended_timer': recommend_optimal_timer(timer_metadata, body_measurements)
            },
            'performance_metrics': {
                'total_processing_time': round(total_processing_time, 2),
                'photo_processing_time': round(photo_processing_time, 2),
                'analysis_time': round(analysis_time, 2),
                'selection_time': round(selection_time, 2)
            }
        }

        session['avatar_result'] = response_data

        try:
            analytics_session = AnalysisSession(
                session_id=session_id,
                timestamp=datetime.now(),
                user_height=height,
                user_weight=weight,
                user_gender=gender,
                analysis_type='enhanced_with_timer',
                selected_mannequin_id=mannequin_result['id'],
                similarity_score=mannequin_result.get('similarity_score', 0.0),
                confidence_score=body_measurements.confidence_score * 100,
                processing_time=total_processing_time,
                photo_count=len(uploaded_photos),
                pose_quality_scores=body_measurements.pose_quality_scores,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr,
                completion_status='success',
                timer_metadata=timer_metadata,
                timer_effectiveness=timer_effectiveness
            )
            
            analytics_manager.log_analysis_session(analytics_session)
        except Exception as e:
            logger.error(f"Failed to log analytics session: {e}")
        
        logger.info(f"Enhanced timer analysis complete for user: {gender}, {height}cm, {weight}kg. "
                   f"Selected: {mannequin_result['filename']} "
                   f"(similarity: {mannequin_result.get('similarity_score', 0):.1f}%, "
                   f"confidence: {body_measurements.confidence_score:.2f}, "
                   f"timer effectiveness: {timer_effectiveness:.1f}%)")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in enhanced timer analyze endpoint: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error during enhanced timer analysis'
        }), 500

@api_bp.route('/partner-inquiry', methods=['POST'])
def partner_inquiry():
    """
    Handles partner form submissions from the landing page.
    """
    try:
        data = request.get_json()
        required = ['name', 'email', 'message']

        for field in required:
            if field not in data or not data[field].strip():
                return jsonify({
                    'success': False,
                    'message': f'{field.title()} is required'
                }), 400

        email = data['email'].strip()
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({
                'success': False,
                'message': 'Please provide a valid email address'
            }), 400

        logger.info(f"New partner inquiry from {data['name']} ({data['email']})")
        logger.info(f"Phone: {data.get('phone', 'Not provided')}")
        logger.info(f"Message: {data['message'][:100]}...")




        
        return jsonify({
            'success': True,
            'message': 'Thank you for your interest! We will contact you soon.'
        })

    except Exception as e:
        logger.error(f"Error processing partner inquiry: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to submit inquiry. Please try again later.'
        }), 500

@api_bp.route('/analytics/timer-usage', methods=['GET'])
def get_timer_analytics():
    """Get timer usage analytics"""
    try:
        days = int(request.args.get('days', 7))

        timer_stats = analytics_manager.get_timer_usage_stats(days)
        
        return jsonify({
            'success': True,
            'timer_analytics': timer_stats,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Timer analytics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate timer analytics'
        }), 500

@api_bp.route('/analytics/timer-effectiveness', methods=['GET'])
def get_timer_effectiveness():
    """Get timer effectiveness metrics"""
    try:
        effectiveness_data = analytics_manager.get_timer_effectiveness_data()
        
        return jsonify({
            'success': True,
            'effectiveness_data': effectiveness_data,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Timer effectiveness analytics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate effectiveness analytics'
        }), 500

@api_bp.route('/analytics/daily-usage', methods=['GET'])
def get_daily_usage():
    """Get daily usage statistics"""
    try:
        days = int(request.args.get('days', 30))
        
        daily_stats = analytics_manager.get_daily_usage_stats(days)
        
        return jsonify({
            'success': True,
            'daily_stats': daily_stats,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Daily usage analytics error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate daily usage analytics'
        }), 500

def preprocess_image_with_timer_data(image_array, timers_used, pose):
    """Enhanced image preprocessing that considers timer usage for optimization"""
    try:

        processed_image = preprocess_image(image_array)

        avg_timer = sum(timers_used) / len(timers_used) if timers_used else 5

        if avg_timer >= 8:

            processed_image = apply_quality_enhancement(processed_image)
        elif avg_timer <= 5:

            processed_image = apply_stabilization_filter(processed_image)
        
        return processed_image
        
    except Exception as e:
        logger.error(f"Error in timer-aware preprocessing: {e}")

        return preprocess_image(image_array)

def apply_quality_enhancement(image):
    """Apply quality enhancement for high-timer photos"""
    try:
        import cv2

        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(image, -1, kernel)

        enhanced = cv2.addWeighted(sharpened, 0.7, image, 0.3, 0)
        
        return enhanced
    except:
        return image

def apply_stabilization_filter(image):
    """Apply stabilization for low-timer photos that might have motion"""
    try:
        import cv2

        stabilized = cv2.GaussianBlur(image, (3, 3), 0.5)
        
        return stabilized
    except:
        return image

def calculate_timer_effectiveness(timer_metadata, body_measurements):
    """Calculate how effective the timer usage was for photo quality"""
    try:
        score = 0

        score += body_measurements.confidence_score * 40

        timers_used = timer_metadata.get('timers_used', [])
        if len(set(timers_used)) == 1:  # Consistent timer usage
            score += 20

        avg_timer = timer_metadata.get('average_timer', 5)
        if 7 <= avg_timer <= 10:  # Sweet spot for positioning
            score += 20
        elif avg_timer >= 5:
            score += 10

        avg_quality = sum(body_measurements.pose_quality_scores.values()) / len(body_measurements.pose_quality_scores)
        score += avg_quality * 20
        
        return min(100, max(0, score))
        
    except Exception as e:
        logger.error(f"Error calculating timer effectiveness: {e}")
        return 50.0  # Default moderate score

def assess_timer_quality_impact(timer_metadata, body_measurements):
    """Assess how timer usage impacted photo quality"""
    try:
        timers_used = timer_metadata.get('timers_used', [])
        avg_timer = sum(timers_used) / len(timers_used) if timers_used else 5
        avg_quality = sum(body_measurements.pose_quality_scores.values()) / len(body_measurements.pose_quality_scores)
        
        if avg_quality > 0.8 and avg_timer >= 8:
            return "excellent"
        elif avg_quality > 0.6 and avg_timer >= 5:
            return "good"
        elif avg_quality > 0.4:
            return "moderate"
        else:
            return "needs_improvement"
            
    except:
        return "unknown"

def recommend_optimal_timer(timer_metadata, body_measurements):
    """Recommend optimal timer setting based on results"""
    try:
        timers_used = timer_metadata.get('timers_used', [])
        avg_quality = sum(body_measurements.pose_quality_scores.values()) / len(body_measurements.pose_quality_scores)

        if avg_quality > 0.7:
            avg_timer = sum(timers_used) / len(timers_used) if timers_used else 5
            return f"{int(avg_timer)}s"

        if avg_quality < 0.5:
            return "10s"

        return "7s"
        
    except:
        return "5s"

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file_storage):
    """Validate uploaded file size"""
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per image
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)  # Reset to beginning
    return size <= MAX_FILE_SIZE

def enhance_image_analyzer():
    """Add timer-aware methods to ImageAnalyzer class"""
    
    def analyze_photos_with_timer_context(self, photos, user_height, user_weight, timer_metadata):
        """Enhanced photo analysis that considers timer context"""
        try:

            measurements = self.analyze_photos(photos, user_height, user_weight)

            if timer_metadata:
                measurements = self.apply_timer_quality_adjustments(measurements, timer_metadata)
            
            return measurements
            
        except Exception as e:
            logger.error(f"Error in timer-aware analysis: {e}")

            return self.analyze_photos(photos, user_height, user_weight)
    
    def apply_timer_quality_adjustments(self, measurements, timer_metadata):
        """Apply timer-based quality adjustments to measurements"""
        try:
            timers_used = timer_metadata.get('timers_used', [])
            avg_timer = sum(timers_used) / len(timers_used) if timers_used else 5

            if avg_timer >= 8:
                measurements.confidence_score *= 1.1
            elif avg_timer <= 4:
                measurements.confidence_score *= 0.9

            for pose, timer_used in zip(measurements.pose_quality_scores.keys(), timers_used):
                if timer_used >= 8 and measurements.pose_quality_scores[pose] < 0.6:

                    measurements.pose_quality_scores[pose] *= 0.8
                elif timer_used <= 5 and measurements.pose_quality_scores[pose] > 0.7:

                    measurements.pose_quality_scores[pose] *= 1.1

            measurements.confidence_score = min(1.0, max(0.0, measurements.confidence_score))
            for pose in measurements.pose_quality_scores:
                measurements.pose_quality_scores[pose] = min(1.0, max(0.0, measurements.pose_quality_scores[pose]))
            
            return measurements
            
        except Exception as e:
            logger.error(f"Error applying timer adjustments: {e}")
            return measurements

    if ENHANCED_ANALYSIS_AVAILABLE:
        from app.image_analysis import ImageAnalyzer
        ImageAnalyzer.analyze_photos_with_timer_context = analyze_photos_with_timer_context
        ImageAnalyzer.apply_timer_quality_adjustments = apply_timer_quality_adjustments

def enhance_mannequin_selector():
    """Add timer-aware methods to EnhancedMannequinSelector class"""
    
    def select_best_mannequin_with_timer_context(self, user_height, user_weight, user_gender, 
                                                body_measurements, timer_metadata):
        """Enhanced selection that considers timer effectiveness"""
        try:

            result = self.select_best_mannequin(user_height, user_weight, user_gender, body_measurements)
            
            if result and timer_metadata:

                timer_effectiveness = calculate_timer_effectiveness(timer_metadata, body_measurements)

                if timer_effectiveness > 80:
                    result['similarity_score'] *= 1.05  # Boost for excellent timer usage
                elif timer_effectiveness < 40:
                    result['similarity_score'] *= 0.95  # Reduce for poor timer usage

                result['timer_effectiveness'] = timer_effectiveness
                result['timer_metadata'] = timer_metadata

                result['similarity_score'] = min(100.0, max(0.0, result['similarity_score']))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in timer-aware selection: {e}")

            return self.select_best_mannequin(user_height, user_weight, user_gender, body_measurements)

    if ENHANCED_ANALYSIS_AVAILABLE:
        from app.image_analysis import EnhancedMannequinSelector
        EnhancedMannequinSelector.select_best_mannequin_with_timer_context = select_best_mannequin_with_timer_context

enhance_image_analyzer()
enhance_mannequin_selector()

logger.info("API routes initialized with timer-enhanced functionality")