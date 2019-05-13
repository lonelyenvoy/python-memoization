from setuptools import setup, find_packages

setup(name='memoization',
      version='0.1.3',
      description='A powerful caching library for Python, with TTL support and multiple algorithm options. '
                  '(https://github.com/lonelyenvoy/python-memoization)',
      keywords='memoization memorization remember decorator cache caching function callable'
               'functional ttl limited capacity fast high-performance optimization',
      url='https://github.com/lonelyenvoy/python-memoization',
      author='lonelyenvoy',
      author_email='petrinchor@gmail.com',
      license='MIT',
      packages=find_packages(),
      exclude_package_data={'': ['examples.py', 'test.py']},
      python_requires='>=2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4')
