from setuptools import setup, find_packages

setup(
    name="uno",
    version="0.1.0",
    description="Microservices micro-framework for NATS",
    author="@appetio",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "nats-py>=2.0.0",
        "logfire",
        "asyncio",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "uno=uno.cli:main",
        ]
    }
)