"""Entry point for the VisionPower desktop app (``visionpower`` console script)."""

from __future__ import annotations

import sys


def main() -> int:
    from PySide6 import QtWidgets

    from visionpower.app.main_window import MainWindow
    from visionpower.app.theme import apply_theme

    app = QtWidgets.QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()  # bring to front so it isn't hidden behind others
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
