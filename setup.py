from setuptools import setup, find_packages

setup(
    name='SnapFlow',
    version='0.0.1',
    packages=find_packages(),
    license='GPLv3',
    install_requires=['pyyaml'],
    scripts=['bin/snap_scheduler'],  # Path to your executable file
)
