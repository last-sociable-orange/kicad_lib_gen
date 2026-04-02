"""
Terminal color utilities for better message visibility.
Provides colored output functions for different message types.
"""


class Colors:
    """ANSI color codes for terminal output."""

    # Standard colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Text styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Reset
    RESET = "\033[0m"


class Styles:
    """Pre-defined message styles."""

    # Message types
    INFO = f"{Colors.BLUE}ℹ{Colors.RESET}"
    SUCCESS = f"{Colors.GREEN}✓{Colors.RESET}"
    WARNING = f"{Colors.YELLOW}⚠{Colors.RESET}"
    ERROR = f"{Colors.RED}✗{Colors.RESET}"
    QUESTION = f"{Colors.CYAN}?{Colors.RESET}"
    ARROW = f"{Colors.CYAN}→{Colors.RESET}"
    BULLET = f"{Colors.DIM}•{Colors.RESET}"
    STAR = f"{Colors.YELLOW}★{Colors.RESET}"

    # Headers
    HEADER = f"{Colors.BOLD}{Colors.CYAN}"
    SUBHEADER = f"{Colors.BOLD}{Colors.WHITE}"


def info(message: str) -> str:
    """Return info-styled message."""
    return f"{Styles.INFO} {message}"


def success(message: str) -> str:
    """Return success-styled message."""
    return f"{Styles.SUCCESS} {Colors.GREEN}{message}{Colors.RESET}"


def warning(message: str) -> str:
    """Return warning-styled message."""
    return f"{Styles.WARNING} {Colors.YELLOW}{message}{Colors.RESET}"


def error(message: str) -> str:
    """Return error-styled message."""
    return f"{Styles.ERROR} {Colors.RED}{message}{Colors.RESET}"


def question(message: str) -> str:
    """Return question-styled message."""
    return f"{Styles.QUESTION} {Colors.CYAN}{message}{Colors.RESET}"


def header(message: str) -> str:
    """Return header-styled message."""
    return f"{Styles.HEADER}{message}{Colors.RESET}"


def subheader(message: str) -> str:
    """Return subheader-styled message."""
    return f"{Styles.SUBHEADER}{message}{Colors.RESET}"


def dim(message: str) -> str:
    """Return dimmed message."""
    return f"{Colors.DIM}{message}{Colors.RESET}"


def highlight(message: str) -> str:
    """Return highlighted message."""
    return f"{Colors.BRIGHT_CYAN}{message}{Colors.RESET}"


def bold(message: str) -> str:
    """Return bold message."""
    return f"{Colors.BOLD}{message}{Colors.RESET}"


def print_info(message: str):
    """Print info message."""
    print(info(message))


def print_success(message: str):
    """Print success message."""
    print(success(message))


def print_warning(message: str):
    """Print warning message."""
    print(warning(message), flush=True)


def print_error(message: str):
    """Print error message."""
    print(error(message), file=sys.stderr, flush=True)


def print_header(message: str):
    """Print header message."""
    print(header(message))


def print_subheader(message: str):
    """Print subheader message."""
    print(subheader(message))


def print_highlight(message: str):
    """Print highlighted message."""
    print(highlight(message))


def print_product_item(index: int, mpn: str, manufacturer: str, description: str, qty: str, status: str) -> str:
    """Format a product list item with consistent styling."""
    # Determine quantity color (handle non-numeric gracefully)
    try:
        qty_int = int(qty)
        qty_color = Colors.GREEN if qty_int > 0 else Colors.RED if qty_int == 0 else Colors.YELLOW
    except ValueError:
        qty_color = Colors.YELLOW

    # Determine status color
    status_upper = status.upper() if status else ""
    status_color = Colors.GREEN if status_upper == "ACTIVE" else Colors.RED if status_upper in ["NOTRECOMMENDED", "OBSOLETE", "DISCONTINUED"] else Colors.YELLOW if status_upper in ["PRELIMINARY", "LASTBUY", "ENDOFLIFE"] else Colors.WHITE

    return (
        f"  {Colors.DIM}[{index}]{Colors.RESET} "
        f"{Colors.BOLD}{Colors.CYAN}{mpn}{Colors.RESET}"
        f"{Colors.DIM} | {Colors.RESET}{manufacturer}"
        f"{Colors.DIM} | {Colors.RESET}{description}"
        f"{Colors.DIM} | Qty: {qty_color}{qty}{Colors.RESET}"
        f"{Colors.DIM} | Status: {status_color}{status}{Colors.RESET}"
    )


def print_selected(mpn: str, manufacturer: str, description: str) -> str:
    """Format selected product message."""
    return (
        f"{Styles.ARROW} Selected: "
        f"{Colors.BOLD}{Colors.GREEN}{mpn}{Colors.RESET}"
        f"{Colors.DIM} ({manufacturer} - {description}){Colors.RESET}"
    )


# Import sys here to avoid circular import issues
import sys
