from setuptools import setup

setup(name = 'hyke',
      version = '0.2.0',
      description = 'Utility to run scripts and capture their output in a '
                    'repeatable way',
      author = 'Marvin Poul',
      author_email = 'ponder@creshal.de',
      license = 'MIT',

      packages = ["hyke"],

      entry_points = {
          'console_scripts': [
              'hyke = hyke:main'
            ],
      },

      python_requires = '>=3.4',
)
