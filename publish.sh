set -e  # if any step fails, kill the entire script and warn the user something went wrong

# get VERSION from args --version=
VERSION=${1/--version=/}

export TWINE_USERNAME=${2/--username=/}
export TWINE_PASSWORD=${3/--password=/}

# echo username and password
echo "${2/--username=/}"
echo "${3/--password=/}"

# in setup.py, replace the line '\tversion=...' with '\tversion={VERSION}'
sed -i.bak "s/version=.*/version='${VERSION}',/" setup.py

# Write the following text out to agentmemory/__init__.py to replace the current (without the comments)
cat << EOF > agentmemory/__init__.py
"""
agentmemory

Simple agent memory, powered by chromadb
"""

__version__ = "${VERSION}"
__author__ = 'Moon (https://github.com/lalalune)'
__credits__ = 'https://github.com/lalalune/agentmemory and https://www.trychroma.com/'
EOF

# Check if these dependencies are installed, and install them if they aren't
pip install twine || echo "Failed to install twine"
pip install wheel || echo "Failed to install wheel"

# Make sure these work, and stop the script if they error
# Run setup checks and build
python setup.py check || { echo "Setup check failed"; exit 1; }
python setup.py sdist || { echo "Source distribution build failed"; exit 1; }
python setup.py bdist_wheel --universal || { echo "Wheel build failed"; exit 1; }

# Make sure these work, and stop the script if they error
# Upload to test repo
twine upload dist/agentmemory-${VERSION}.tar.gz --repository-url https://test.pypi.org/legacy/ || { echo "Upload to test repo failed"; exit 1; }
pip install --index-url https://test.pypi.org/simple/ agentmemory --user || { echo "Installation from test repo failed"; exit 1; }

# Final upload
twine upload dist/* || { echo "Final upload failed"; exit 1; }
pip install agentmemory --user || { echo "Installation of agentmemory failed"; exit 1; }

# Let the user know that everything completed successfully
echo "Script completed successfully"
