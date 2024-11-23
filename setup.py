from setuptools import find_packages, setup

package_name = 'needlePenetrationRobot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'PyQt5'],
    zip_safe=True,
    maintainer='ayou1',
    maintainer_email='ayou1@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'crtk_test = needlePenetrationRobot.crtk_test:main',
            'gui = needlePenetrationRobot.gui:main',
        ],
    },
)