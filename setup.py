#!/usr/bin/env python3
"""
Setup script for Ucursito - U-Cursos Scraper
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README for long description
readme_file = Path(__file__).parent / 'README.md'
long_description = ''
if readme_file.exists():
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='ucursito',
    version='0.2.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='U-Cursos scraper and calendar exporter',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/iaaaanb/ucursos-scraper',

    # Package discovery
    packages=find_packages(include=['src', 'src.*']),

    # Include additional files
    package_data={
        'src': ['*.py'],
    },

    # Python modules (for config.py in root)
    py_modules=['config'],

    # Python version requirement
    python_requires='>=3.8',

    # Dependencies
    install_requires=requirements,

    # Entry points - creates 'ucursito' command
    entry_points={
        'console_scripts': [
            'ucursito=ucursito_wrapper:main',
        ],
    },

    # Additional scripts
    scripts=['ucursito'],

    # Classification
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Topic :: Education',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],

    # Keywords
    keywords='ucursos scraper calendar ics universidad chile',

    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/iaaaanb/ucursos-scraper/issues',
        'Source': 'https://github.com/iaaaanb/ucursos-scraper',
    },
)
