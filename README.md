#Setup backend

##Start virtal environment call it 'ENV'
```
virtualenv ENV
source ENV/bin/activate
```
##install the modules
```
ENV/bin/pip install -r requirements.txt
```
##Install lastest pycoin lib from my clone
```
pip install git+https://github.com/lekanovic/pycoin.git@latest
```
##bcrypt latest
```
pip install git+https://github.com/pyca/bcrypt.git@v1.1.1
```
##create an freeze of installed items
```
ENV/bin/pip freeze > requirements.txt
```
##install modules directly from github.
```
pip install git+https://github.com/trezor/python-mnemonic.git@master
```

#Run
```
git clone git@github.com:lekanovic/bitcoin.git
cd bitcoin
virtualenv ENV
source ENV/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/picunia
#Start blockchainfetcher. This python process will monitor all new block 
#it will scan all the transactions look for bitcoin addresses that belongs
#to Picunia clients. When Picunia addresses are found blockchainfetcher
#will update the balance for each client i the database.
#
# start blockchainfetcher
python picunia/network/blockchainfetcher.py &
#
#
#Start celery server
#Celery server will take incomming requests like create new account
#pay-to-address etc.
celery worker -A celery_task -l debug -Ofair -f logfile.out
```
