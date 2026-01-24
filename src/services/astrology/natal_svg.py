"""Natal chart SVG generation and PNG conversion.

Creates visual representation of natal chart with:
- Zodiac wheel (12 signs)
- Planet positions
- House cusps
- Aspect lines between planets
"""

import asyncio
import math

import cairosvg
import svgwrite
import structlog

from src.services.astrology.natal_chart import FullNatalChartResult

logger = structlog.get_logger()

# Color scheme (dark theme)
BACKGROUND_COLOR = "#1a1a2e"
WHEEL_COLOR = "#4a4e69"
SIGN_COLOR = "#c9a227"  # Gold for zodiac symbols
TEXT_COLOR = "#f2e9e4"
HOUSE_LINE_COLOR = "#4a4e69"

# Planet colors for visibility
PLANET_COLORS = {
    "sun": "#FFD700",      # Gold
    "moon": "#C0C0C0",     # Silver
    "mercury": "#FFA500",  # Orange
    "venus": "#FFB6C1",    # Pink
    "mars": "#FF4444",     # Red
    "jupiter": "#9370DB",  # Purple
    "saturn": "#808080",   # Gray
    "uranus": "#00CED1",   # Cyan
    "neptune": "#4B0082",  # Indigo
    "pluto": "#8B0000",    # Dark red
    "north_node": "#32CD32",  # Green
}

# Planet Unicode glyphs (professional astrological symbols)
PLANET_GLYPHS = {
    "sun": "\u2609",       # Sun symbol
    "moon": "\u263D",      # First quarter moon
    "mercury": "\u263F",   # Mercury
    "venus": "\u2640",     # Venus
    "mars": "\u2642",      # Mars
    "jupiter": "\u2643",   # Jupiter
    "saturn": "\u2644",    # Saturn
    "uranus": "\u2645",    # Uranus
    "neptune": "\u2646",   # Neptune
    "pluto": "\u2647",     # Pluto
    "north_node": "\u260A",  # Ascending Node
}

# Zodiac sign Unicode glyphs
ZODIAC_GLYPHS = [
    "\u2648",  # Aries
    "\u2649",  # Taurus
    "\u264A",  # Gemini
    "\u264B",  # Cancer
    "\u264C",  # Leo
    "\u264D",  # Virgo
    "\u264E",  # Libra
    "\u264F",  # Scorpio
    "\u2650",  # Sagittarius
    "\u2651",  # Capricorn
    "\u2652",  # Aquarius
    "\u2653",  # Pisces
]

# Aspect colors
ASPECT_COLORS = {
    "Conjunction": "#32CD32",  # Green (harmonious)
    "Sextile": "#4169E1",      # Blue (harmonious)
    "Square": "#FF4444",       # Red (challenging)
    "Trine": "#4169E1",        # Blue (harmonious)
    "Opposition": "#FF4444",   # Red (challenging)
}


def _lon_to_angle(longitude: float, offset: float = 0) -> float:
    """Convert ecliptic longitude to angle for drawing.

    In SVG, 0 degrees is at 3 o'clock (right), counter-clockwise.
    We want Aries (0 degrees) at 9 o'clock (left), going clockwise.

    Args:
        longitude: Ecliptic longitude (0-360)
        offset: Additional rotation offset

    Returns:
        Angle in radians for SVG drawing
    """
    # SVG angles: 0 = right, goes counter-clockwise
    # We want: Aries at top-left (9 o'clock), zodiac goes counter-clockwise
    angle = 180 - longitude + offset
    return math.radians(angle)


def _polar_to_cart(cx: float, cy: float, r: float, angle_rad: float) -> tuple[float, float]:
    """Convert polar to Cartesian coordinates.

    Args:
        cx: Center X
        cy: Center Y
        r: Radius
        angle_rad: Angle in radians

    Returns:
        (x, y) Cartesian coordinates
    """
    x = cx + r * math.cos(angle_rad)
    y = cy - r * math.sin(angle_rad)  # SVG Y is inverted
    return x, y


def _generate_svg(chart_data: FullNatalChartResult, size: int = 800) -> str:
    """Generate SVG string for natal chart.

    Args:
        chart_data: Full natal chart data
        size: Image size in pixels (default 800 for better detail)

    Returns:
        SVG string
    """
    dwg = svgwrite.Drawing(size=(size, size))
    center = size / 2
    outer_r = size / 2 - 30  # Increased margin for 800px
    sign_r = outer_r - 35  # Radius for sign labels
    inner_r = outer_r - 60  # Inner edge of zodiac band
    planet_r = inner_r - 40  # Radius for planets
    house_r = inner_r - 80  # Inner circle for houses

    # === DEFS: Gradients ===
    # Background: cosmic radial gradient (dark center, lighter edges)
    bg_grad = dwg.radialGradient(center=("50%", "50%"), r="70%", id="bg")
    bg_grad.add_stop_color(0, "#0a0a14")     # Deep space center
    bg_grad.add_stop_color(0.5, "#1a1a2e")   # Current dark blue
    bg_grad.add_stop_color(1, "#252542")     # Lighter edge
    dwg.defs.add(bg_grad)

    # Zodiac band: linear gradient for depth
    zodiac_grad = dwg.linearGradient(start=("0%", "0%"), end=("100%", "100%"), id="zodiac_band")
    zodiac_grad.add_stop_color(0, "#3d3d5c")
    zodiac_grad.add_stop_color(1, "#2d2d44")
    dwg.defs.add(zodiac_grad)

    # Planet glow gradients (gold for Sun/Jupiter, silver for others)
    for name, color in [("gold", "#FFD700"), ("silver", "#C0C0C0")]:
        glow = dwg.radialGradient(id=f"glow_{name}")
        glow.add_stop_color(offset=0, color=color, opacity=1.0)
        glow.add_stop_color(offset=0.5, color=color, opacity=0.25)
        glow.add_stop_color(offset=1, color=color, opacity=0)
        dwg.defs.add(glow)

    # Background with gradient
    dwg.add(dwg.rect((0, 0), (size, size), fill="url(#bg)"))

    # Zodiac band fill (between outer_r and inner_r)
    dwg.add(dwg.circle(
        center=(center, center),
        r=outer_r,
        fill="url(#zodiac_band)"
    ))
    # Cut out center to create ring effect
    dwg.add(dwg.circle(
        center=(center, center),
        r=inner_r,
        fill="url(#bg)"
    ))

    # Outer circle (zodiac wheel border)
    dwg.add(dwg.circle(
        center=(center, center),
        r=outer_r,
        stroke=WHEEL_COLOR,
        fill="none",
        stroke_width=2
    ))

    # Inner circle border
    dwg.add(dwg.circle(
        center=(center, center),
        r=inner_r,
        stroke=WHEEL_COLOR,
        fill="none",
        stroke_width=1
    ))

    # House circle
    dwg.add(dwg.circle(
        center=(center, center),
        r=house_r,
        stroke=HOUSE_LINE_COLOR,
        fill="none",
        stroke_width=1
    ))

    # Draw zodiac sign divisions (12 signs, 30 degrees each)
    for i in range(12):
        angle = _lon_to_angle(i * 30)
        x1, y1 = _polar_to_cart(center, center, inner_r, angle)
        x2, y2 = _polar_to_cart(center, center, outer_r, angle)
        dwg.add(dwg.line((x1, y1), (x2, y2), stroke=WHEEL_COLOR, stroke_width=1))

        # Zodiac sign glyph at midpoint
        mid_angle = _lon_to_angle(i * 30 + 15)
        sx, sy = _polar_to_cart(center, center, sign_r, mid_angle)
        dwg.add(dwg.text(
            ZODIAC_GLYPHS[i],
            insert=(sx, sy),
            text_anchor="middle",
            dominant_baseline="middle",
            fill=SIGN_COLOR,
            font_size=14,
            font_family="DejaVu Sans, Symbola, Arial, sans-serif"
        ))

    # Draw house cusps (if time known, all 12 houses)
    if chart_data["time_known"]:
        for house_num, house_data in chart_data["houses"].items():
            cusp_lon = house_data["cusp"]
            angle = _lon_to_angle(cusp_lon)
            x1, y1 = _polar_to_cart(center, center, house_r - 10, angle)
            x2, y2 = _polar_to_cart(center, center, inner_r, angle)

            # Main angles (1, 4, 7, 10) are thicker
            stroke_width = 2 if house_num in (1, 4, 7, 10) else 1
            dwg.add(dwg.line(
                (x1, y1), (x2, y2),
                stroke=HOUSE_LINE_COLOR,
                stroke_width=stroke_width
            ))

    # Draw aspect lines between planets (only top 10 for readability)
    top_aspects = chart_data["aspects"][:10]
    for aspect in top_aspects:
        p1_lon = chart_data["planets"][aspect["planet1"]]["longitude"]
        p2_lon = chart_data["planets"][aspect["planet2"]]["longitude"]

        angle1 = _lon_to_angle(p1_lon)
        angle2 = _lon_to_angle(p2_lon)

        x1, y1 = _polar_to_cart(center, center, planet_r, angle1)
        x2, y2 = _polar_to_cart(center, center, planet_r, angle2)

        color = ASPECT_COLORS.get(aspect["aspect"], "#666666")
        # Opacity based on orb (tighter = more visible)
        opacity = max(0.3, 1 - aspect["orb"] / 8)

        line = dwg.line(
            (x1, y1), (x2, y2),
            stroke=color,
            stroke_width=1.5,
            stroke_opacity=opacity
        )
        line["stroke-linecap"] = "round"
        dwg.add(line)

    # Draw planets with glow effect
    for planet_name, planet_data in chart_data["planets"].items():
        lon = planet_data["longitude"]
        angle = _lon_to_angle(lon)
        px, py = _polar_to_cart(center, center, planet_r, angle)

        color = PLANET_COLORS.get(planet_name, "#FFFFFF")
        glyph = PLANET_GLYPHS.get(planet_name, "?")

        # Determine glow color based on planet
        glow_type = "gold" if planet_name in ("sun", "jupiter") else "silver"

        # Draw glow (larger, behind main circle)
        dwg.add(dwg.circle(
            center=(px, py),
            r=20,
            fill=f"url(#glow_{glow_type})"
        ))

        # Main planet circle (smaller, on top)
        dwg.add(dwg.circle(
            center=(px, py),
            r=12,
            fill=color,
            fill_opacity=0.9
        ))

        # Planet glyph
        dwg.add(dwg.text(
            glyph,
            insert=(px, py),
            text_anchor="middle",
            dominant_baseline="middle",
            fill="#000000",
            font_size=14,
            font_weight="bold",
            font_family="DejaVu Sans, Symbola, Arial, sans-serif"
        ))

    # Ascendant marker with glow effect
    if chart_data["time_known"]:
        asc_lon = chart_data["angles"]["ascendant"]["longitude"]
        asc_angle = _lon_to_angle(asc_lon)
        ax1, ay1 = _polar_to_cart(center, center, outer_r + 5, asc_angle)
        ax2, ay2 = _polar_to_cart(center, center, outer_r + 20, asc_angle)

        # Glow effect for ASC marker
        dwg.add(dwg.circle(
            center=(ax2, ay2),
            r=12,
            fill="url(#glow_gold)"
        ))
        asc_line = dwg.line(
            (ax1, ay1), (ax2, ay2),
            stroke="#FF6B6B",
            stroke_width=3
        )
        asc_line["stroke-linecap"] = "round"
        dwg.add(asc_line)
        dwg.add(dwg.text(
            "ASC",
            insert=(ax2, ay2 - 8),
            text_anchor="middle",
            fill="#FF6B6B",
            font_size=10,
            font_weight="bold",
            font_family="DejaVu Sans, Arial, sans-serif"
        ))

        # MC marker with glow effect
        mc_lon = chart_data["angles"]["mc"]["longitude"]
        mc_angle = _lon_to_angle(mc_lon)
        mx1, my1 = _polar_to_cart(center, center, outer_r + 5, mc_angle)
        mx2, my2 = _polar_to_cart(center, center, outer_r + 20, mc_angle)

        # Glow effect for MC marker
        dwg.add(dwg.circle(
            center=(mx2, my2),
            r=12,
            fill="url(#glow_silver)"
        ))
        mc_line = dwg.line(
            (mx1, my1), (mx2, my2),
            stroke="#4ECDC4",
            stroke_width=3
        )
        mc_line["stroke-linecap"] = "round"
        dwg.add(mc_line)
        dwg.add(dwg.text(
            "MC",
            insert=(mx2, my2 - 8),
            text_anchor="middle",
            fill="#4ECDC4",
            font_size=10,
            font_weight="bold",
            font_family="DejaVu Sans, Arial, sans-serif"
        ))

    return dwg.tostring()


async def generate_natal_png(
    chart_data: FullNatalChartResult,
    size: int = 800,
) -> bytes:
    """Generate natal chart as PNG image.

    Args:
        chart_data: Full natal chart data
        size: Image size in pixels (default 800 for professional detail)

    Returns:
        PNG image bytes
    """
    try:
        # Generate SVG
        svg_string = _generate_svg(chart_data, size)

        # Convert to PNG in thread (CPU-bound)
        png_bytes = await asyncio.to_thread(
            cairosvg.svg2png,
            bytestring=svg_string.encode("utf-8"),
            output_width=size,
            output_height=size,
        )

        logger.debug(
            "natal_png_generated",
            size=size,
            bytes_len=len(png_bytes),
        )

        return png_bytes

    except Exception as e:
        logger.error("natal_png_error", error=str(e))
        raise
