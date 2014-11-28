from setuptools import setup, find_packages


DEPENDENCIES = [
    'PyYAML',
    'requests'
]

TEST_DEPENDENCIES = [
    'nose',
    'mock'
]


setup(
    name='juju-onlinelabs',
    version='0.0.1',
    author='Edouard Bonlieu',
    author_email='ebonlieu@ocs.online.net',
    description='Online Labs integration with juju',
    url='http://onlinelabs.net',
    license='BSD',
    packages=find_packages(),
    install_requires=DEPENDENCIES,
    tests_require=DEPENDENCIES + TEST_DEPENDENCIES,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent'
    ],
    entry_points={
        'console_scripts': [
            'juju-onlinelabs = juju_onlinelabs.cli:main'
        ]
    }
)
