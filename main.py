"""CLI entrypoint for WeGlide NZ client - wrapper that calls app/main"""

import sys
import os

# Add path to app
_app_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_app_path, 'app'))

# Import and run the actual main from app, passing args
from app.main import main as _main
_main(sys.argv[1:])