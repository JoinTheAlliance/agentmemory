from setuptools import setup

setup(
    name='agentmemory',
    version='0.1.3',
    description='Dead simple agent memory, powered by chromadb',
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
