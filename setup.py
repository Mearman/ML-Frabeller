from setuptools import setup

with open("README.md", "r") as fh:
	long_description = fh.read()

setup(
	name="ML-Fabeller",
	version="1.0",
	author="Joseph Mearman",
	description="A tooled at labelleing video frames for ML training",
	url="https://github.com/Mearman/ML-Frabeller",
	python_requires='>=3.6',
	install_requires=["pandas", "opencv-python", "numpy"]
)