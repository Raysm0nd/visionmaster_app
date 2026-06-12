"""Line-icon factory — SVG paths transcribed from the approved AXON design.

Each icon is the inner markup of a 24×24 viewBox; ``__C__`` is a colour
placeholder substituted at render time. Stroked shapes inherit the svg-level
stroke; filled shapes set ``fill="__C__" stroke="none"`` explicitly. Icons are
rendered to crisp pixmaps via QtSvg, so they scale to any size/colour.
"""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtSvg

# name -> inner SVG markup (paths/circles/rects/text). __C__ = colour.
ICONS: dict[str, str] = {
    "save": '<path d="M5 4h10l4 4v12H5z"/><path d="M8 4v5h6"/>'
            '<rect x="8" y="13" width="8" height="7" rx="1"/>',
    "open": '<path d="M3 7h6l2 2h10v9H3z"/>',
    "export": '<path d="M12 15V5"/><path d="M8 9l4-4 4 4"/><path d="M5 19h14"/>',
    "import": '<path d="M12 5v10"/><path d="M8 11l4 4 4-4"/><path d="M5 19h14"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/>'
            '<path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "camera": '<path d="M3 8h3.5l1.8-2h7.4l1.8 2H21v11H3z"/>'
              '<circle cx="12" cy="13" r="3.4"/>',
    "library": '<rect x="4" y="4" width="7" height="7" rx="1.4"/>'
               '<rect x="13" y="4" width="7" height="7" rx="1.4"/>'
               '<rect x="4" y="13" width="7" height="7" rx="1.4"/>'
               '<rect x="13" y="13" width="7" height="7" rx="1.4"/>',
    "var": '<text x="12" y="15.5" text-anchor="middle" font-size="9" '
           'font-family="monospace" font-weight="600" fill="__C__" '
           'stroke="none">var</text>',
    "str": '<text x="12" y="15.5" text-anchor="middle" font-size="9" '
           'font-family="monospace" font-weight="600" fill="__C__" '
           'stroke="none">STR</text>',
    "cube": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12v9"/>'
            '<path d="M20 7.5L12 12 4 7.5"/>',
    "aim": '<circle cx="12" cy="12" r="7.5"/><circle cx="12" cy="12" r="2.6"/>'
           '<path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
    "code": '<path d="M9 8l-4 4 4 4"/><path d="M15 8l4 4-4 4"/>',
    "play": '<path d="M8 5.5l11 6.5-11 6.5z" fill="__C__" stroke="none"/>',
    "step": '<path d="M7 5.5l9 6.5-9 6.5z" fill="__C__" stroke="none"/>'
            '<path d="M18 5v14"/>',
    "scan": '<path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8"/>'
            '<path d="M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8"/>'
            '<path d="M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16"/>'
            '<path d="M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16"/><path d="M4 12h16"/>',
    "ruler": '<path d="M4 14L14 4l6 6L10 20z"/>'
             '<path d="M8 10l2 2M11 7l2 2M14 13l1 1"/>',
    "clock": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
    "sliders": '<path d="M4 8h9M17 8h3M4 16h3M11 16h9"/>'
               '<circle cx="15" cy="8" r="2"/><circle cx="9" cy="16" r="2"/>',
    "layers": '<path d="M12 4l8 4-8 4-8-4z"/><path d="M4 12l8 4 8-4"/>'
              '<path d="M4 16l8 4 8-4"/>',
    "bucket": '<path d="M7 4l9 9-6 6-7-7z"/><path d="M10 13l6-3"/>'
              '<path d="M18 14l2 3a2 2 0 1 1-4 0z" fill="__C__" stroke="none"/>',
    "chart": '<path d="M5 5v14h14"/><path d="M8 15v-3M12 15V9M16 15v-5"/>',
    "image": '<rect x="4" y="5" width="16" height="14" rx="2.4"/>'
             '<circle cx="9" cy="10" r="1.8"/><path d="M5 17l5-4 4 3 3-2 3 3"/>',
    "pencil": '<path d="M5 19l1.3-4.3L16 5l3 3L9.3 17.7z"/><path d="M14 7l3 3"/>',
    "branch": '<circle cx="7" cy="6" r="2"/><circle cx="7" cy="18" r="2"/>'
              '<circle cx="17" cy="9" r="2"/><path d="M7 8v8"/>'
              '<path d="M7 13a6 6 0 0 0 6-4"/>',
    "send": '<path d="M4 12L20 5l-7 15-2-6z"/><path d="M11 14l3-3"/>',
    "blob": '<path d="M12 4c4.2 0 6 3.2 4.8 6.6 1 1 2.2 1.8 2.2 4 0 3-3 5.4-7 '
            '5.4S5 17.4 5 13.8c0-2.8 1.6-4 1.6-4C5.4 6.8 7.6 4 12 4z"/>'
            '<circle cx="10.5" cy="12" r="1" fill="__C__" stroke="none"/>'
            '<circle cx="14" cy="14" r="1" fill="__C__" stroke="none"/>',
    "ocr": '<path d="M5 18L9 6l4 12"/><path d="M6.4 14h5.2"/><path d="M16 6v12"/>'
           '<path d="M16 6h3.2"/><path d="M16 12h2.6"/>',
    "search": '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.2-4.2"/>'
              '<path d="M11 8.5v5M8.5 11h5"/>',
    "zoomout": '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.2-4.2"/>'
               '<path d="M8.5 11h5"/>',
    "onetoone": '<text x="12" y="15.5" text-anchor="middle" font-size="9" '
                'font-family="monospace" font-weight="600" fill="__C__" '
                'stroke="none">1:1</text>',
    "fullscreen": '<path d="M4 9V4h5"/><path d="M20 9V4h-5"/>'
                  '<path d="M4 15v5h5"/><path d="M20 15v5h-5"/>',
    "split": '<rect x="4" y="5" width="16" height="14" rx="1.6"/>'
             '<path d="M12 5v14"/>',
    "grid": '<rect x="4" y="4" width="16" height="16" rx="1.6"/>'
            '<path d="M4 12h16M12 4v16"/>',
    "min": '<path d="M5 12h14"/>',
    "max": '<rect x="6" y="6" width="12" height="12" rx="1.6"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "gear": '<circle cx="12" cy="12" r="3"/>'
            '<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1'
            'M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
    "cloud": '<path d="M7 18a4 4 0 0 1-.4-8A5.2 5.2 0 0 1 16.7 9.4 '
             '3.6 3.6 0 0 1 18 16.5"/>',
    "plus": '<path d="M12 6v12M6 12h12"/>',
    "chevleft": '<path d="M14 6l-6 6 6 6"/>',
    "chevright": '<path d="M10 6l6 6-6 6"/>',
    "chevdown": '<path d="M7 10l5 5 5-5"/>',
    "network": '<circle cx="6" cy="7" r="2"/><circle cx="18" cy="7" r="2"/>'
               '<circle cx="12" cy="17" r="2"/>'
               '<path d="M7.5 8.4L11 15.4M16.5 8.4L13 15.4M8 7h8"/>',
    "warn": '<path d="M12 4l8.5 15H3.5z"/><path d="M12 10v4"/>'
            '<circle cx="12" cy="17.4" r="0.5" fill="__C__" stroke="none"/>',
    "runcircle": '<circle cx="12" cy="12" r="8.4"/>'
                 '<path d="M10.4 8.6l5.2 3.4-5.2 3.4z" fill="__C__" stroke="none"/>',
}

_DOT = '<circle cx="12" cy="12" r="2.4" fill="__C__" stroke="none"/>'


def _svg_bytes(name: str, color: str) -> QtCore.QByteArray:
    inner = ICONS.get(name, _DOT).replace("__C__", color)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    )
    return QtCore.QByteArray(svg.encode("utf-8"))


def make_pixmap(name: str, color: str = "#C2CCDA", size: int = 18) -> QtGui.QPixmap:
    """Render icon ``name`` to a transparent ``size``×``size`` pixmap in ``color``."""

    renderer = QtSvg.QSvgRenderer(_svg_bytes(name, color))
    dpr = 2  # render at 2x for crisp edges on hidpi
    pm = QtGui.QPixmap(size * dpr, size * dpr)
    pm.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def make_icon(name: str, color: str = "#C2CCDA", size: int = 18) -> QtGui.QIcon:
    """Return a ``QIcon`` for icon ``name``; unknown names fall back to a dot."""

    return QtGui.QIcon(make_pixmap(name, color, size))
