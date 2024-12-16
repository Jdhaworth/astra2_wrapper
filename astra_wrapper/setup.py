from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'astra_wrapper'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, ['resource/requirements.txt']),
        (os.path.join('share', package_name, 'images'), glob('images/*')),  # Include images folder
    ],
    package_data={package_name: ['*.py']},
    install_requires=[
        'setuptools', 
        'opencv-python',
        'numpy<=2.1.3',
        'open3d==0.18.0',
        'opencv_contrib_python==4.6.0.66',
        'opencv_python==4.10.0.84',
        'plyfile==1.1',
        'pyorbbecsdk==1.3.2',
        'ultralytics==8.3.28'
    ],
    zip_safe=True,
    maintainer='jesse-imerse',
    maintainer_email='jesse-imerse@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'start_astra = astra_wrapper.start_astra:main',
        ],
    },
)

