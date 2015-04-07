from setuptools import setup, find_packages


DEPENDENCIES = [
    'PyYAML',
    'requests',
    'ndg-httpsclient >=0.3.3',
]

TEST_DEPENDENCIES = [
    'mock'
]


setup(
    name='juju-scaleway',
    version='0.1.0',
    author='Scaleway',
    author_email='opensource@scaleway.com',
    description='Scaleway integration with juju',
    url='http://www.scaleway.com',
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
            'juju-scaleway = juju_scaleway.cli:main'
        ]
    }
)
