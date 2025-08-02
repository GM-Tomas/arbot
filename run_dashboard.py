#!/usr/bin/env python3
"""
Launcher script for the Real-Time Crypto Price Dashboard
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to launch the dashboard"""
    try:
        logger.info("Starting Real-Time Crypto Price Dashboard...")
        
        # Import and run the Dash app
        from web.app import app
        
        logger.info("Dashboard is starting...")
        logger.info("Access the dashboard at: http://localhost:8050")
        logger.info("Press Ctrl+C to stop the dashboard")
        
        # Run the app
        app.run_server(
            debug=False,  # Set to True for development
            host='0.0.0.0',
            port=8050,
            dev_tools_hot_reload=False
        )
        
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 