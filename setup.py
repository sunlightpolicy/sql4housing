from distutils.core import setup
setup(
  name = 'sql4housing',         # How you named your package folder (MyLib)
  packages = ['sql4housing'],   # Chose the same as "name"
  version = 'v0.0.2-alpha',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Create housing databases with a command line interface.',   # Give a short description about your library
  author = 'Krista Chan',                   # Type in your name
  author_email = 'kristacchan@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/sunlightpolicy/sql4housing',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/sunlightpolicy/sql4housing/archive/v0.0.2-alpha.tar.gz',    # I explain this later on
  keywords = ['CIVIC-TECH', 'HOUSING-DATA', 'HOUSING_ADVOCATES', 'CITIES', 'DATABASES', 'SODA', 'CENSUS', 'HUD', 'HOUSING', 'POSTGIS'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'numpy',
          'pandas',
          'sodapy',
          'shapely',
          'sqlalchemy',
          'sqlalchemy_utils',
          'geoalchemy2',
          'docopt',
          'requests',
          'progress',
          'geomet',
          'pyshp',
          'psycopg2',
          'python-Levenshtein',
          'cenpy',
          'pyyaml'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)