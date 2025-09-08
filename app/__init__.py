import logging
import os
from flask import Flask, render_template
from .services import initialize_mannequins
from .api.routes import api_bp
from .routes import main_bp

def create_app():
    """Application factory to create and configure the Flask app."""
    
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'dev-key-for-development'

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    MODELS_PATH = os.path.join(APP_ROOT, 'models', 'smpl')
    STATIC_MANNEQUINS_PATH = os.path.join(APP_ROOT,'static')

    with app.app_context():
        initialize_mannequins(model_path=MODELS_PATH, 
            output_dir=os.path.join(STATIC_MANNEQUINS_PATH, 'mannequins')
        )

    @app.errorhandler(404)
    def not_found_error(error):

        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):

        return render_template('500.html'), 500

    return app