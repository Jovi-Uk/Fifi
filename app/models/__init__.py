
"""
Models package for Avatar Analyzer application.
This file makes the models directory a Python package and provides
convenient imports for the mannequin-related classes.
"""

from .mannequins import (
    UserMeasurements,
    MannequinResult,
    MannequinService,
    get_mannequin_service
)

__all__ = [
    'UserMeasurements',
    'MannequinResult', 
    'MannequinService',
    'get_mannequin_service'
]

__version__ = '1.0.0'
__author__ = 'Fifi Development Team'