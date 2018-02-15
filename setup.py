import pip
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

# NoseTestCommand allow to launch nosetest with the command 'python setup.py test'
class NoseTestCommand(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Run nose ensuring that argv simulates running nosetests directly
        import nose
        nose.run_exit(argv=['nosetests'])

setup(name='eikon',
      version='0.1.11',
      description='Python package for retrieving Eikon data.',
      long_description='Python package for retrieving Eikon data.',
      url='https://developers.thomsonreuters.com/tr-eikon-scripting-apis/python-thin-library-pyeikon/',
      author='Thomson Reuters',
      author_email='',
      license='LICENSE',
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      use_2to3=True,
      zip_safe=False,
      install_requires=['requests',
                        'datetime',
                        'pandas>=0.17.0',
                        'appdirs',
                        'python-dateutil',
                        'websocket-client'],
      test_suite='nose.collector',
      tests_require=['nose', 'mock', 'lettuce'],
      cmdclass={'test': NoseTestCommand}
)
