from setuptools import setup, find_packages

setup(name='juju-onlinelabs',
      version="0.0.1",
      classifiers=[
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Operating System :: OS Independent'],
      author='Edouard Bonlieu',
      author_email='ebonlieu@ocs.online.net',
      description="Online Labs integration with juju",
      url='http://onlinelabs.net',
      license='BSD',
      packages=find_packages(),
      install_requires=["PyYAML", "requests"],
      tests_require=["nose", "mock"],
      entry_points={
          "console_scripts": [
              'juju-onlinelabs = juju_onlinelabs.cli:main']},
      )
