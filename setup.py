from setuptools import setup, find_packages

setup(
    name='gcptools',
    version='0.1.0',
    description='Outils pour la gestion de Google Cloud Platform',
    url='git@github.com:tomy137/gcptools.git',
    author='Thomas Auvray',
    author_email='thomas.auvray@gmail.com',
    packages=find_packages(),
    zip_safe=False,
 	install_requires=[
        'dateparser',
        'fsspec',
        'gcsfs',
        'google-api-python-client',
        'google-cloud-compute',
        'google-cloud-pubsub',
        'google-cloud-storage',
        'google-cloud-tasks',
        'google.cloud.logging',
        'oauth2client',
        'Pillow',
        'pymysql',
        'pytz',
        'requests',
        'sqlalchemy',
        'tzlocal',
        'unidecode',
        'mysql-connector-python'
      ]
)

