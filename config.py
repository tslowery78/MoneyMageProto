"""
Configuration for MoneyMage file paths.

All input/output files are stored in iCloud for automatic backup.
The code repository stays clean with just source code.
"""
import os
from pathlib import Path

# ============================================================================
# iCloud Base Paths
# ============================================================================

# iCloud Drive base path on macOS
ICLOUD_BASE = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs"

# MoneyMage data folder in iCloud
MONEYMAGE_DATA = ICLOUD_BASE / "MoneyMage"

# ============================================================================
# Input/Output Directories
# ============================================================================

# Where your budget files, transactions, and auto_categories live
INPUTS_DIR = MONEYMAGE_DATA / "inputs"

# Where archives and generated outputs go
OUTPUTS_DIR = MONEYMAGE_DATA / "outputs"

# Archive directory for backups (inside outputs)
ARCHIVE_DIR = OUTPUTS_DIR / "archive"

# ============================================================================
# Default File Paths
# ============================================================================

def get_budget_path(year: int = 2025) -> Path:
    """Get the path to the budget file for a given year."""
    return INPUTS_DIR / f"Budget_{year}.xlsx"


def get_transactions_path() -> Path:
    """Get the path to the transactions file."""
    return INPUTS_DIR / "transactions.xlsx"


def get_auto_categories_path() -> Path:
    """Get the path to the auto_categories file."""
    return INPUTS_DIR / "auto_categories.xlsx"


def get_archive_dir() -> Path:
    """Get the archive directory path, creating it if needed."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    return ARCHIVE_DIR


def get_downloads_dir() -> Path:
    """Get the downloads directory for bank CSV imports."""
    # You can change this to wherever your bank CSVs are downloaded
    return Path.home() / "Downloads"


# ============================================================================
# Initialization - Ensure directories exist
# ============================================================================

def ensure_directories():
    """Create the MoneyMage directories if they don't exist."""
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"MoneyMage data directories ready:")
    print(f"  Inputs:  {INPUTS_DIR}")
    print(f"  Outputs: {OUTPUTS_DIR}")
    print(f"  Archive: {ARCHIVE_DIR}")


# Run on import to ensure directories exist
if __name__ == "__main__":
    ensure_directories()


