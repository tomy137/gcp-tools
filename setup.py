from setuptools import setup, find_packages

setup(
    name='gcptools',
    version='0.0.1',
    description='Outils pour la gestion de Google Cloud Platform',
    url='git@github.com:tomy137/gcptools.git',
    author='Thomas Auvray',
    author_email='thomas.auvray@gmail.com',
    packages=find_packages(),
    zip_safe=False,
 	install_requires=[
        'pymysql~=1.0',
        'sqlalchemy~=1.4',
        'Pillow~=9.2',
        'google-cloud-tasks',
        'google-cloud-storage',
        'google-cloud-pubsub==2.4.*',
        'google.cloud.logging',
        'google-api-python-client',
        'oauth2client',
        'markupsafe==2.0.1',
        'requests',
        'gcsfs',
        'fsspec',
        'unidecode',
        'dateparser',
        'Pillow',
        'tzlocal==2.1',
        'pytz'
      ]
)

