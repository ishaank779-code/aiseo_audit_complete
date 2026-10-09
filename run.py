#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 50021))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
