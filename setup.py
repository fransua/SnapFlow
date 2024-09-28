from setuptools import setup, find_packages

setup(
    name='SnapFlow',
    version='0.0.1',
    packages=find_packages(),
    license='GPLv3',
    install_requires=['pyyaml', 'python_mermaid'],
    scripts=['bin/snap_scheduler'],  # Path to your executable file
)
