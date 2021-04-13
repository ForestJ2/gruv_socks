import setuptools


setuptools.setup(
    name='gruv_socks',
    version='0.9.7',
    url="https://github.com/ForestJ2/gruv_socks",
    author="Forest Jacobsen",
    description="Easy to use standard for abstracting the work needed to transport and reconstruct messages over TCP.",
    packages=setuptools.find_packages(include=['gruv_socks', 'gruv_socks.*']),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
