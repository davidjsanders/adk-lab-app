"""SVG and Base64 chart/widget generators for interactive system cards."""

import base64
from typing import Dict

MATERIAL_ICONS: Dict[str, str] = {
    "dns": "M20,13H4C2.9,13,2,13.9,2,15v4c0,1.1,0.9,2,2,2h16c1.1,0,2-0.9,2-2v-4C22,13.9,21.1,13,20,13z M20,19H4v-4h16V19z M20,3H4 C2.9,3,2,3.9,2,5v4c0,1.1,0.9,2,2,2h16c1.1,0,2-0.9,2-2V5C22,3.9,21.1,3,20,3z M20,9H4V5h16V9z",
    "business_center": "M20 7h-4V5c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 5h4v2h-4V5zm10 14H4V9h16v10z",
    "article": "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-4-4H9v-2h6v2zm-2-4H9V9h4v2z",
    "confirmation_number": "M22 10V6c0-1.11-.9-2-2-2H4c-1.1 0-1.99.89-1.99 2v4c1.1 0 1.99.9 1.99 2s-.89 2-2 2v4c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-4c-1.1 0-2-.9-2-2s.9-2 2-2zm-9 7.5h-2v-2h2v2zm0-4.5h-2v-2h2v2zm0-4.5h-2v-2h2v2z",
    "computer": "M20 18c1.1 0 1.99-.9 1.99-2L22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z",
    "history": "M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"
}


def generate_donut_chart(percentage: float, label: str = "") -> str:
    """Generates a Base64-encoded SVG circular donut progress chart.

    Args:
        percentage: The progress percentage value (0.0 to 100.0).
        label: Text sub-label printed inside center of circle.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    percentage = max(0.0, min(100.0, percentage))
    free = 100.0 - percentage

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <circle cx="40" cy="44" r="18" fill="#0B131E" />
  <circle cx="40" cy="44" r="18" fill="transparent" stroke="#EF4444" stroke-width="4.5" />
  <circle cx="40" cy="44" r="18" fill="transparent" stroke="#22C55E" stroke-width="4.5" stroke-dasharray="{free * 1.13097} {percentage * 1.13097}" stroke-dashoffset="28.27" />
  <text x="40" y="15" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  <text x="40" y="46.5" font-family="sans-serif" font-size="7" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{percentage:.1f}%</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def generate_horizontal_bar(percentage: float, label: str, val_text: str) -> str:
    """Generates a Base64-encoded SVG horizontal progress bar.

    Args:
        percentage: The progress percentage value (0.0 to 100.0).
        label: Text label describing the progress bar.
        val_text: Raw display value text printed adjacent to the label.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    percentage = max(0.0, min(100.0, percentage))
    fill_width = percentage * 0.6

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <text x="40" y="18" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  <rect x="10" y="34" width="60" height="7" rx="3.5" fill="#1F2937" />
  <rect x="10" y="34" width="{fill_width}" height="7" rx="3.5" fill="#38BDF8" />
  <text x="40" y="58" font-family="sans-serif" font-size="7.5" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{val_text}</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def generate_range_gauge(
    value: float,
    max_value: float,
    label: str,
    val_text: str,
    yellow_threshold: float,
    red_threshold: float
) -> str:
    """Generates a Base64-encoded SVG range gauge scale with a pointer indicator.

    Args:
        value: Current metric value.
        max_value: Target maximum bounds of the scale (maps to 100% width).
        label: Metric label description.
        val_text: Display value string.
        yellow_threshold: Yellow warning boundary metric value.
        red_threshold: Red critical boundary metric value.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    percentage = (value / max_value) * 100.0 if max_value > 0 else 0.0
    percentage = max(0.0, min(100.0, percentage))

    yellow_pct = (yellow_threshold / max_value) * 100.0 if max_value > 0 else 50.0
    red_pct = (red_threshold / max_value) * 100.0 if max_value > 0 else 80.0

    ptr_x = 10 + (percentage * 0.6)

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <text x="40" y="18" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  
  <rect x="10" y="38" width="{yellow_pct * 0.6}" height="6" fill="#22C55E" rx="3" />
  <rect x="{10 + yellow_pct * 0.6}" y="38" width="{(red_pct - yellow_pct) * 0.6}" height="6" fill="#EAB308" />
  <rect x="{10 + red_pct * 0.6}" y="38" width="{(100 - red_pct) * 0.6}" height="6" fill="#EF4444" rx="3" />
  
  <polygon points="{ptr_x},36 {ptr_x - 3},30 {ptr_x + 3},30" fill="#FFFFFF" />
  <text x="40" y="58" font-family="sans-serif" font-size="7.5" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{val_text}</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def generate_status_pill(label: str, val_text: str, status: str) -> str:
    """Generates a Base64-encoded SVG status banner pill with a custom icon.

    Args:
        label: Status metric label description.
        val_text: Formatted display text state.
        status: One of 'healthy', 'warning', or 'critical'.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    if status == "healthy":
        border_color, text_color, bg_color = "#22C55E", "#86EFAC", "#064E3B"
        icon_path = "M5 13l4 4L19 7"
    elif status == "warning":
        border_color, text_color, bg_color = "#F59E0B", "#FDE68A", "#78350F"
        icon_path = "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
    else:  # critical or unknown
        border_color, text_color, bg_color = "#EF4444", "#FCA5A5", "#7F1D1D"
        icon_path = "M6 18L18 6M6 6l12 12"

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <text x="40" y="18" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  
  <rect x="25" y="28" width="30" height="30" rx="15" fill="{bg_color}" stroke="{border_color}" stroke-width="1" />
  <svg x="33" y="36" width="14" height="14" viewBox="0 0 24 24">
    <path d="{icon_path}" stroke="{text_color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
  </svg>
  
  <text x="40" y="68" font-family="sans-serif" font-size="7" fill="{text_color}" text-anchor="middle" font-weight="bold">{val_text}</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def generate_material_icon_svg(icon_name: str, fill_color: str = "#38BDF8") -> str:
    """Generates a Base64-encoded Data URI for a Google Material Design Icon SVG path.

    Args:
        icon_name: Name of the Google Font icon (e.g. 'dns', 'business_center', 'article').
        fill_color: Hex color string.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    path_d = MATERIAL_ICONS.get(icon_name, MATERIAL_ICONS["business_center"])
    svg = f"""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="{path_d}" fill="{fill_color}" />
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def generate_number_widget(label: str, val_text: str) -> str:
    """Generates a Base64-encoded SVG card showing a prominent numeric value/text.

    Args:
        label: Description header of the numeric metric.
        val_text: Display string of the numeric value (e.g. "5 entries", "12 users").

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    val_len = len(val_text)
    val_font_size = 8.0 if val_len > 12 else (10.0 if val_len > 8 else 12.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <text x="40" y="20" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  <text x="40" y="52" font-family="sans-serif" font-size="{val_font_size}" fill="#38BDF8" text-anchor="middle" font-weight="bold">{val_text}</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def generate_traffic_light_svg(status: str) -> str:
    """Generates a Base64-encoded Data URI for a dynamic traffic light SVG.

    Args:
        status: The system health status string.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    red_color = "#7F1D1D"     # Saturated dull red
    amber_color = "#78350F"   # Saturated dull amber
    green_color = "#064E3B"   # Saturated dull green

    if status == "HEALTHY":
        green_color = "#00FF66"  # Brighter electric green
    elif status == "DEGRADED":
        amber_color = "#F59E0B"
    else:  # UNHEALTHY, REBOOTING, etc.
        red_color = "#EF4444"

    svg = f"""<svg width="14" height="36" viewBox="0 0 14 36" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="1" y="1" width="12" height="34" rx="3" fill="#111827" stroke="#374151" stroke-width="1"/>
  <circle cx="7" cy="7" r="3.2" fill="{red_color}"/>
  <circle cx="7" cy="18" r="3.2" fill="{amber_color}"/>
  <circle cx="7" cy="29" r="3.2" fill="{green_color}"/>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"
