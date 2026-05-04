#!/usr/bin/env python3
"""
Movie Odyssey — Terminal film manager
Entry point: python3 movie_odyssey.py
"""

import sys
from ui import run


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C anywhere
        print("\n\n  Goodbye.\n")
        sys.exit(0)
