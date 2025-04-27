from setuptools import setup, find_packages

setup(
    name="submarine-tracker",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.5.0",
        "geopandas>=0.9.0",
        "shapely>=1.7.0",
        "folium>=0.14.0",
        "pydeck>=0.7.0",
        "matplotlib>=3.4.0",
        "requests>=2.26.0",
        "python-dotenv>=0.19.0",
    ],
) 