# Virtual Environment Setup Guide

This guide explains how to set up a virtual environment for the MoneyMageProto project.

## Creating a Virtual Environment

### Windows

```bash
# Navigate to your project directory
cd path\to\MoneyMageProto

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# or
pip install -e .
```

### macOS/Linux

```bash
# Navigate to your project directory
cd path/to/MoneyMageProto

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# or
pip install -e .
```

## Using the Virtual Environment

After activation, you'll see `(venv)` at the beginning of your command prompt, indicating that the virtual environment is active. Any Python packages you install will be isolated to this environment.

### Running the Application

With the virtual environment activated:

```bash
python BudgetMeeting.py -y 2025 -b Budget_2025.xlsx -t transactions.xlsx
```

### Deactivating the Environment

When you're done working, you can deactivate the virtual environment:

```bash
deactivate
```

## Maintaining Dependencies

If you add new packages to the project:

1. Install them with pip while the virtual environment is active
2. Update the requirements.txt file:

```bash
pip freeze > requirements.txt
```

## Troubleshooting

### Package Installation Issues

If you experience issues installing packages:

```bash
# Upgrade pip
pip install --upgrade pip

# Try installing with verbose output
pip install -r requirements.txt -v
```

### Virtual Environment Not Activating

Make sure you've created the virtual environment in the correct location and are using the correct activation command for your operating system.

### Excel Library Issues

If you encounter issues with the Excel libraries:

```bash
# Reinstall Excel libraries
pip uninstall openpyxl xlsxwriter
pip install openpyxl==3.1.2 xlsxwriter==3.1.2
``` 