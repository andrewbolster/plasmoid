from setuptools import setup

setup(
    name='plasmoid',
    version='0.1',
    packages=['plasmoid'],
    url='bolster.online',
    license='MIT',
    author='Andrew Bolster',
    author_email='me@andrewbolster.info',
    entry_points={'console_scripts':[
        'plasmoid=plasmoid.__main__:launch']
    },
    description='MQTT Client for Desk Display integrating PiLite Scrolling serial display and Grove LCD Text Display.'
)
