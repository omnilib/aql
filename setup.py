from setuptools import setup

with open("README.md") as f:
    readme = f.read()

with open("aql/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split('"')[1]

setup(
    name="aql",
    description="asyncio query generator",
    long_description=readme,
    long_description_content_type="text/markdown",
    version=version,
    author="John Reese",
    author_email="john@noswap.com",
    url="https://github.com/jreese/aql",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries",
    ],
    license="MIT",
    packages=["aql", "aql.tests"],
    setup_requires=["setuptools>=38.6.0"],
    install_requires=[],
)
