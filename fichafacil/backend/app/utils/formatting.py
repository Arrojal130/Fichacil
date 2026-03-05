"""
FichaFacil MVP - Formatting Utilities
Common formatting functions shared across routers.
"""


def format_hours(minutes: int) -> str:
    """Format minutes as 'Xh Ym' string.
    
    Args:
        minutes: Total minutes to format
        
    Returns:
        Formatted string like '8h 30m'
    """
    if minutes < 0:
        return "0h 0m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"
