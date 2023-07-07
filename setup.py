from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()
    long_description=long_description,  # added this line
    long_description_content_type="text/markdown",  # and this line

setup(
    name='agentmemory',
    version='0.1.4',
    description='Easy-to-use agent memory, powered by chromadb',
    url='https://github.com/lalalune/agentmemory',
    author='Moon',
    author_email='shawmakesmagic@gmail.com',
    license='MIT',
    packages=['agentmemory'],
    install_requires=['chromadb'],
    readme = "README.md",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 3',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows'
    ],
)
