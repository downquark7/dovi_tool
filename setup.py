from setuptools import setup, find_packages

setup(
    name="dovi-to-hdr10plus",
    version="1.0.0",
    description="Extract HDR10+ metadata from Dolby Vision RPU using heuristics and ML",
    author="HDR Conversion Tool",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
        "scikit-learn>=1.0.0",
        "scipy>=1.7.0",
        "matplotlib>=3.5.0",
        "pandas>=1.3.0",
        "json5>=0.9.0",
        "Pillow>=8.3.0",
        "tqdm>=4.62.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "dovi-to-hdr10plus=dovi_to_hdr10plus.cli:main",
        ],
    },
)