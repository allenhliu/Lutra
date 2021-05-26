from setuptools import setup, find_packages
setup(
    name="lutra",
    version="1.0.1",
    description='Lutra Automation Runner',
    packages=find_packages(),
    install_requires=['pytest >= 6.1.1', 'selenium', 'requests', 'allure-pytest >= 2.8.18', 'pytest-bdd >= 4.0.1',
                      'pytest-xdist', 'pytest-rerunfailures', 'opencv-python', 'numpy'],
    author='jacejiang',
    python_requires='>=3',
)
