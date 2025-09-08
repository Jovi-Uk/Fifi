"""
Main routes for serving frontend pages.
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    """Serve the main avatar analyzer page."""
    return render_template('pseudo_clanding.html')

@main_bp.route('/demo')
def demo():
    """Serves the data entry form page (your index.html)."""
    return render_template('index.html')

@main_bp.route('/report')
def report():
    """Serve the 3D avatar report page."""
    return render_template('report.html')

