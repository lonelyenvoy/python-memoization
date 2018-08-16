from setuptools import setup, find_packages

setup(name='memoization',
      version='0.0.9',
      description='A minimalist functional caching lib for Python, with TTL and auto memory management support. '
                  '(https://github.com/lonelyenvoy/python-memoization)',
      keywords='memoization memorization remember decorator cache caching function callable'
               'functional ttl limited capacity fast high-performance optimization',
      url='https://github.com/lonelyenvoy/python-memoization',
      author='lonelyenvoy',
      author_email='petrinchor@gmail.com',
      license='MIT',
      packages=find_packages(),
      exclude_package_data={'': ['examples.py', 'test.py']})
