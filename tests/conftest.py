import sys
from pathlib import Path

# Add the project root to the Python path for test discovery
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
