# Instructions

### Start virtal environment call it 'ENV'
virtualenv ENV
source ENV/bin/activate

### install the modules
ENV/bin/pip install -r requirements.txt

### Install lastest pycoin lib from my clone
pip install git+https://github.com/lekanovic/pycoin.git@latest

### bcrypt latest
pip install git+https://github.com/pyca/bcrypt.git@v1.1.1

### create an freeze of installed items
ENV/bin/pip freeze > requirements.txt

### install modules directly from github.
prepend "git+"
add branch name "@master"
pip install git+https://github.com/trezor/python-mnemonic.git@master
