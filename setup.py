from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='memoization',
    version='0.1.4',
    description='A powerful caching library for Python, with TTL support and multiple algorithm options. '
                '(https://github.com/lonelyenvoy/python-memoization)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='memoization memorization remember decorator cache caching function callable'
             'functional ttl limited capacity fast high-performance optimization',
    url='https://github.com/lonelyenvoy/python-memoization',
    author='lonelyenvoy',
    author_email='petrinchor@gmail.com',
    license='MIT',
    packages=find_packages(),
    exclude_package_data={'': ['examples.py', 'test.py']},
    python_requires='>=2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
