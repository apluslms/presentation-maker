from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    # Note that some requirements which are from github are in dependency_links below
    requirements = f.read().splitlines()

setup(
    name="presentation_maker",
    version="0.0.1",
    author="Juuso Vuorenmaa",
    author_email="juuso.vuorenmaa@aalto.fi",
    description="Tool for making HTML & PDF presentations from A+ course materials written in ReStructuredText.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Aalto-LeTech/presentation-maker.git",
    packages=find_packages(),
    python_requires='>=3.6',
    package_data={
        'presentation_maker': ['*.css', '*.style', 'presentation_config.yaml', 'deck2pdf-0.3.0/*/*']
    },
    install_requires=requirements,
    entry_points={
        'console_scripts': ['presentation_maker = presentation_maker.presentation_maker:main'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
    ],
)
