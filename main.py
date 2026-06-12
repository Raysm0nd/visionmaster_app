"""Convenience launcher: ``python main.py`` starts the desktop app.

The real entry point is ``visionpower.app.main:main`` (also installed as the
``visionpower`` console script).
"""

from visionpower.app.main import main

if __name__ == "__main__":
    raise SystemExit(main())
