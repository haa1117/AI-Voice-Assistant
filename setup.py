from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="assistx",
    version="1.0.0",
    author="AssistX Development Team",
    author_email="dev@assistx.com",
    description="AI Voice Assistant for Medical Clinics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/assistx/assistx",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.json"],
        "templates": ["*.html"],
        "static": ["**/*"],
    },
    entry_points={
        "console_scripts": [
            "assistx=main:main",
        ],
    },
) 