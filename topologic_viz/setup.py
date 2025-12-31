"""
TopologicViz - Visualization library for TopologicPy

Installation:
    pip install -e .
    
    Or with Bokeh support:
    pip install -e ".[bokeh]"
"""

from setuptools import setup, find_packages

setup(
    name="topologic_viz",
    version="0.1.0",
    description="Visualization adapters for TopologicPy bubble diagrams and graphs",
    author="arlav_Theo_Dounas",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20",
    ],
    extras_require={
        "bokeh": [
            "bokeh>=3.0",
        ],
        "matplotlib": [
            "matplotlib>=3.5",
        ],
        "all": [
            "bokeh>=3.0",
            "matplotlib>=3.5",
            "topologicpy",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
