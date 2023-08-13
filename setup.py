from setuptools import setup

long_description = ""
with open("README.md", "r") as fh:
    long_description = fh.read()
    long_description = long_description.split('\n')
    long_description = [line for line in long_description if not '<img' in line]
    long_description = '\n'.join(long_description)
    
install_requires = [
    "chromadb",
    "agentlogger",
    "psycopg2-binary",
    "python-dotenv"
]

setup(
    name='agentmemory',
    version='0.4.8',
    description='Easy-to-use memory for agents, document search, knowledge graphing and more.',
    long_description=long_description,  # added this line
    long_description_content_type="text/markdown",  # and this line
    url='https://github.com/AutonomousResearchGroup/agentmemory',
    author='Moon',
    author_email='shawmakesmagic@gmail.com',
    license='MIT',
    packages=['agentmemory'],
    install_requires=install_requires,
    readme = "README.md",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 3',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows'
    ],
)
