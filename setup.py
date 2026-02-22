# setup.py

from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='nikobusconnect',
    version='1.0.0',
    author='Frederic Debrus',
    author_email='fdebrus@hotmail.com',
    description='A Python library for connecting to Nikobus systems',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fdebrus/nikobusconnect',
    packages=find_packages(),
    install_requires=[
        'pyserial-asyncio>=0.5',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Home Automation',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
