from setuptools import find_packages, setup

subpackages = [
    f"millitrix.{package}"
    for package in find_packages(".")
    if package != "millitrix"
]

setup(
    name="millitrix",
    version="0.0.1",
    packages=["millitrix", *subpackages],
    package_dir={"millitrix": "."},
    include_package_data=True,
)
