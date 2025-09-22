#!/usr/bin/env python3
"""
ECG Monitor Application Launcher
This script launches the ECG Monitor application from the root directory.
"""

import sys
import os

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Change to the src directory
os.chdir(src_dir)

# Import and run the main application
try:
    from main import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"❌ Error importing main application: {e}")
    print("💡 Make sure you're running from the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error running application: {e}")
    sys.exit(1)
