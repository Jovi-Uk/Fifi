
"""
Analytics module for Avatar Analyzer
Tracks timer usage, photo quality, and system performance
"""

import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import os

logger = logging.getLogger(__name__)

@dataclass
class AnalysisSession:
    """Data structure for analysis session tracking"""
    session_id: str
    timestamp: datetime
    user_height: float
    user_weight: float
    user_gender: str
    analysis_type: str  # 'basic' or 'enhanced_with_timer'
    selected_mannequin_id: int
    similarity_score: float
    confidence_score: float
    processing_time: float
    photo_count: int
    pose_quality_scores: Dict[str, float]
    user_agent: str
    ip_address: str
    completion_status: str  # 'success', 'error', 'cancelled'

    timer_metadata: Optional[Dict] = None
    timer_effectiveness: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisSession':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class AnalyticsManager:
    """
    Manages analytics data collection and reporting for the Avatar Analyzer
    """
    
    def __init__(self, data_dir: str = './analytics_data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.sessions_file = self.data_dir / 'sessions.jsonl'
        self.timer_stats_file = self.data_dir / 'timer_stats.json'

        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize analytics files if they don't exist"""
        if not self.sessions_file.exists():
            self.sessions_file.touch()
        
        if not self.timer_stats_file.exists():
            with open(self.timer_stats_file, 'w') as f:
                json.dump({
                    'total_timer_sessions': 0,
                    'timer_5s_usage': 0,
                    'timer_10s_usage': 0,
                    'average_effectiveness': 0.0,
                    'last_updated': datetime.now().isoformat()
                }, f)
    
    def log_analysis_session(self, session: AnalysisSession):
        """Log an analysis session"""
        try:

            with open(self.sessions_file, 'a') as f:
                f.write(json.dumps(session.to_dict()) + '\n')

            if session.timer_metadata:
                self._update_timer_stats(session)
                
            logger.info(f"Analytics session logged: {session.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to log analytics session: {e}")
    
    def _update_timer_stats(self, session: AnalysisSession):
        """Update timer usage statistics"""
        try:
            with open(self.timer_stats_file, 'r') as f:
                stats = json.load(f)

            stats['total_timer_sessions'] += 1
            
            if session.timer_metadata:
                timers_used = session.timer_metadata.get('timers_used', [])
                stats['timer_5s_usage'] += timers_used.count(5)
                stats['timer_10s_usage'] += timers_used.count(10)

            if session.timer_effectiveness:
                current_avg = stats['average_effectiveness']
                total_sessions = stats['total_timer_sessions']
                new_avg = ((current_avg * (total_sessions - 1)) + session.timer_effectiveness) / total_sessions
                stats['average_effectiveness'] = new_avg
            
            stats['last_updated'] = datetime.now().isoformat()
            
            with open(self.timer_stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update timer stats: {e}")
    
    def get_timer_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get timer usage statistics for the last N days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            timer_sessions = []
            with open(self.sessions_file, 'r') as f:
                for line in f:
                    if line.strip():
                        session_data = json.loads(line)
                        session_date = datetime.fromisoformat(session_data['timestamp'])
                        
                        if (session_date >= cutoff_date and 
                            session_data.get('timer_metadata')):
                            timer_sessions.append(session_data)

            total_sessions = len(timer_sessions)
            timer_5s_count = 0
            timer_10s_count = 0
            effectiveness_scores = []
            
            for session in timer_sessions:
                timer_meta = session.get('timer_metadata', {})
                timers_used = timer_meta.get('timers_used', [])
                timer_5s_count += timers_used.count(5)
                timer_10s_count += timers_used.count(10)
                
                if session.get('timer_effectiveness'):
                    effectiveness_scores.append(session['timer_effectiveness'])
            
            avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0
            
            return {
                'period_days': days,
                'total_timer_sessions': total_sessions,
                'timer_5s_usage': timer_5s_count,
                'timer_10s_usage': timer_10s_count,
                'timer_5s_percentage': (timer_5s_count / max(timer_5s_count + timer_10s_count, 1)) * 100,
                'timer_10s_percentage': (timer_10s_count / max(timer_5s_count + timer_10s_count, 1)) * 100,
                'average_effectiveness': round(avg_effectiveness, 1),
                'most_popular_timer': '5s' if timer_5s_count > timer_10s_count else '10s'
            }
            
        except Exception as e:
            logger.error(f"Error getting timer usage stats: {e}")
            return {
                'error': 'Failed to retrieve timer statistics',
                'period_days': days,
                'total_timer_sessions': 0
            }
    
    def get_timer_effectiveness_data(self) -> Dict[str, Any]:
        """Get timer effectiveness analysis"""
        try:
            effectiveness_by_timer = {'5s': [], '10s': []}
            quality_by_timer = {'5s': [], '10s': []}
            
            with open(self.sessions_file, 'r') as f:
                for line in f:
                    if line.strip():
                        session_data = json.loads(line)
                        timer_meta = session_data.get('timer_metadata', {})
                        
                        if timer_meta and session_data.get('timer_effectiveness'):
                            avg_timer = timer_meta.get('average_timer', 5)
                            timer_key = '5s' if avg_timer <= 7.5 else '10s'
                            
                            effectiveness_by_timer[timer_key].append(session_data['timer_effectiveness'])

                            pose_qualities = session_data.get('pose_quality_scores', {})
                            if pose_qualities:
                                avg_quality = sum(pose_qualities.values()) / len(pose_qualities)
                                quality_by_timer[timer_key].append(avg_quality * 100)

            result = {}
            for timer in ['5s', '10s']:
                effectiveness = effectiveness_by_timer[timer]
                quality = quality_by_timer[timer]
                
                result[timer] = {
                    'average_effectiveness': round(sum(effectiveness) / len(effectiveness), 1) if effectiveness else 0,
                    'average_quality': round(sum(quality) / len(quality), 1) if quality else 0,
                    'session_count': len(effectiveness)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting effectiveness data: {e}")
            return {'5s': {'average_effectiveness': 0, 'average_quality': 0, 'session_count': 0},
                    '10s': {'average_effectiveness': 0, 'average_quality': 0, 'session_count': 0}}
    
    def get_daily_usage_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily usage statistics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            daily_stats = {}
            
            with open(self.sessions_file, 'r') as f:
                for line in f:
                    if line.strip():
                        session_data = json.loads(line)
                        session_date = datetime.fromisoformat(session_data['timestamp'])
                        
                        if session_date >= cutoff_date:
                            date_key = session_date.date().isoformat()
                            
                            if date_key not in daily_stats:
                                daily_stats[date_key] = {
                                    'date': date_key,
                                    'total_sessions': 0,
                                    'timer_sessions': 0,
                                    'basic_sessions': 0,
                                    'average_similarity': 0,
                                    'similarities': []
                                }
                            
                            daily_stats[date_key]['total_sessions'] += 1
                            daily_stats[date_key]['similarities'].append(session_data.get('similarity_score', 0))
                            
                            if session_data.get('timer_metadata'):
                                daily_stats[date_key]['timer_sessions'] += 1
                            else:
                                daily_stats[date_key]['basic_sessions'] += 1

            result = []
            for date_key in sorted(daily_stats.keys()):
                stats = daily_stats[date_key]
                if stats['similarities']:
                    stats['average_similarity'] = round(sum(stats['similarities']) / len(stats['similarities']), 1)
                del stats['similarities']  # Remove raw data
                result.append(stats)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting daily usage stats: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up analytics data older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            temp_file = self.sessions_file.with_suffix('.tmp')
            
            kept_sessions = 0
            with open(self.sessions_file, 'r') as infile, open(temp_file, 'w') as outfile:
                for line in infile:
                    if line.strip():
                        session_data = json.loads(line)
                        session_date = datetime.fromisoformat(session_data['timestamp'])
                        
                        if session_date >= cutoff_date:
                            outfile.write(line)
                            kept_sessions += 1

            temp_file.replace(self.sessions_file)
            
            logger.info(f"Analytics cleanup complete. Kept {kept_sessions} sessions.")
            return kept_sessions
            
        except Exception as e:
            logger.error(f"Error during analytics cleanup: {e}")
            return 0