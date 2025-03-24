from setuptools import setup, find_packages

setup(
    name="MoneyMageProto",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.1.0",
        "openpyxl>=3.1.2",
        "xlsxwriter>=3.1.2",
        "numpy>=1.26.0",
    ],
    python_requires='>=3.8',
) 