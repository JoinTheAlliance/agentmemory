set -e  # if any step fails, kill the entire script and warn the user something went wrong

# get VERSION from args --version=
VERSION=${1/--version=/}

# if VERSION contains a v, remove it
VERSION=${VERSION/v/}

export TWINE_USERNAME=${2/--username=/}
export TWINE_PASSWORD=${3/--password=/}

# in setup.py, replace the line '\tversion=...' with '\tversion={VERSION}'
sed -i.bak "s/version=.*/version='${VERSION}',/" setup.py

# remove setup.py.bak
rm "setup.py.bak"

# Read agentmemory/__init__.py, find the line that starts with __version__ and replace with '__version__ = "${VERSION}"'
sed -i.bak "s/__version__.*/__version__ = \"${VERSION}\"/" agentmemory/__init__.py
rm agentmemory/__init__.py.bak

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
twine upload dist/agentmemory-${VERSION}.tar.gz || { echo "Final upload failed"; exit 1; }
pip install agentmemory --user || { echo "Installation of agentmemory failed"; exit 1; }

git add agentmemory/__init__.py
git add setup.py
git commit -m "Updated to ${VERSION} and published"
git push origin main

# Let the user know that everything completed successfully
echo "Script completed successfully"
