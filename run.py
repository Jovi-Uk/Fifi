#!/usr/bin/env python3
"""
run.py - Main entry point for the Fifi Avatar Analyzer Flask application

This file serves as the primary way to start your Flask application.
It can be run directly from the command line:
    python run.py
    
Or with environment variables:
    FLASK_ENV=development python run.py
    FLASK_DEBUG=1 python run.py
"""

import os
import sys
import logging
from pathlib import Path


project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app

def setup_logging():
    """
    Configure logging for the application.
    This helps with debugging and monitoring the application's behavior.
    """

    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    log_file = log_dir / 'fifi_app.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("=" * 60)
    logging.info("Starting Fifi Avatar Analyzer Application")
    logging.info("=" * 60)

def get_config():
    """
    Determine the configuration to use based on environment variables.
    This allows different settings for development, testing, and production.
    """

    flask_env = os.environ.get('FLASK_ENV', 'development')

    config_map = {
        'development': 'development',
        'testing': 'testing',
        'production': 'production'
    }
    
    config_name = config_map.get(flask_env, 'development')
    logging.info(f"Using configuration: {config_name}")
    
    return config_name

def main():
    """
    Main function that creates and runs the Flask application.
    This is the entry point when the script is run directly.
    """

    setup_logging()
    
    try:

        app = create_app()

        host = os.environ.get('FLASK_HOST', '127.0.0.1')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']

        if debug:
            app.config['TEMPLATES_AUTO_RELOAD'] = True
            app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
            logging.info("Debug mode is ON - Templates will auto-reload")

        logging.info(f"Starting Flask application on {host}:{port}")
        logging.info(f"Debug mode: {debug}")
        logging.info(f"Python version: {sys.version}")

        mannequins_path = project_root / 'static' / 'mannequins' / 'mannequin_metadata.json'
        if not mannequins_path.exists():
            logging.warning("Mannequin metadata not found! Run generate_mannequins.py to create them.")
            print("\n" + "="*60)
            print("WARNING: Mannequins not generated yet!")
            print("Please run: python generate_mannequins.py")
            print("="*60 + "\n")
        else:
            logging.info("Mannequin metadata found - application ready")

        print("\n" + "="*60)
        print(f"🚀 Fifi Avatar Analyzer is starting...")
        print(f"🌐 Access the application at: http://{host}:{port}")
        print(f"📊 Debug mode: {debug}")
        print(f"📁 Project root: {project_root}")
        print("="*60 + "\n")


        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,  # Auto-reload on code changes in debug mode
            use_debugger=debug   # Enable debugger in debug mode
        )
        
    except Exception as e:
        logging.error(f"Failed to start application: {e}", exc_info=True)
        print(f"\n❌ Error starting application: {e}")
        print("Check the logs for more details.")
        sys.exit(1)

if __name__ == '__main__':
    """
    This block runs when the script is executed directly.
    It's the standard Python pattern for making scripts executable.
    """
    main()
else:
    """
    This block runs when the module is imported.
    Useful for WSGI servers that need the app object.
    """

    app = create_app()

