#!/usr/bin/env python3
"""
Setup script for Cross-Platform Video Device Control Tool
"""

from setuptools import setup, find_packages
import os
import sys

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Platform-specific requirements
install_requires = ['opencv-python>=4.5.0']

if sys.platform == "win32":
    install_requires.append('pywin32>=227')
elif sys.platform == "linux":
    install_requires.append('v4l2-python>=0.2.0')
elif sys.platform == "darwin":
    install_requires.extend(['pyobjc>=8.0', 'pyobjc-framework-AVFoundation>=8.0'])

setup(
    name="cross-platform-video-control",
    version="1.0.0",
    author="yaoian",
    author_email="30451884+yaoian@users.noreply.github.com",
    description="Cross-platform video device control tool compatible with v4l2-ctl",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yaoian/cross-platform-video-control",
    packages=find_packages(),
    py_modules=[
        'video_device_controller',
        'windows_directshow', 
        'opencv_fallback',
        'v4l2_ctl_cross'
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux", 
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: System :: Hardware",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'black>=21.0.0',
            'flake8>=3.8.0',
            'mypy>=0.900',
        ],
        'test': [
            'pytest>=6.0.0',
            'pytest-cov>=2.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'v4l2-ctl-cross=v4l2_ctl_cross:main',
            'video-control=v4l2_ctl_cross:main',
        ],
    },
    keywords=[
        'video', 'camera', 'v4l2', 'directshow', 'cross-platform', 
        'opencv', 'device-control', 'multimedia', 'webcam'
    ],
    project_urls={
        "Bug Reports": "https://github.com/yaoian/cross-platform-video-control/issues",
        "Source": "https://github.com/yaoian/cross-platform-video-control",
        "Documentation": "https://github.com/yaoian/cross-platform-video-control/blob/main/README.md",
    },
    include_package_data=True,
    zip_safe=False,
)
