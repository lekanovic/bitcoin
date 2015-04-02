# -*- coding: utf-8 -*-
import argparse, sys
import random
import os
import subprocess
import urllib, json
import json



def fill_database():
    url = "http://api.randomuser.me"
    response = urllib.urlopen(url);
    data = json.loads(response.read())

    name = data["results"][0]["user"]["name"]["first"]
    lastname = data["results"][0]["user"]["name"]["last"]
    passwd = data["results"][0]["user"]["password"]
    email = data["results"][0]["user"]["email"]

    add_account(name, lastname, email, passwd)

def find_account_index(index):
    cmd = "python cc.py -i %s" % index
    proc = subprocess.Popen([cmd],
                    stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    return json.loads(out)

def get_number_of_accounts():
    cmd = "python cc.py -n"
    proc = subprocess.Popen([cmd],
                    stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return int(out)

def add_account(name, lastname, email, passwd):
    cmd = "python cc.py -a %s:%s:%s:%s" % (name, lastname, email, passwd)
    proc = subprocess.Popen([cmd],
                    stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    print out

def get_all_accounts():
    proc = subprocess.Popen(["python cc.py -l"],
                    stdout=subprocess.PIPE, shell=True)

    (out, err) = proc.communicate()
    return json.loads(out)['accounts']

def find_account_with_balance():
    a=[]
    for d in get_all_accounts():
        if d['wallet-balance'] > 0:
            a.append(d)
    index = random.randrange(0, len(a))
    return a[index], a[index]['wallet-balance']

def find_random_account():
    rnd = str(random.randrange(0, get_number_of_accounts()))
    return find_account_index(rnd)

def generate_accounts(n):
    nr = get_number_of_accounts()
    for idx in range(nr, nr+n):
        fill_database()

def one_round():
    sender, balance = find_account_with_balance()
    receiver = find_random_account()
    amount = balance / 10

    print "%s sending %d to %s" % (sender['email'], amount, receiver['email'])

    send_from_to(sender['email'], receiver['email'], amount)

def send_from_to(from_email, to_email, amount):
    cmd = "python cc.py -s %s:%s:%s" % (from_email, to_email, amount)
    os.system(cmd)

def main(argv):
    msg = "Test that simulates new accounts created. Simulates user sending Satoshis between them."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-g","--generate",
        help="Generate random user accounts. Input: int - number of accounts to create")
    parser.add_argument("-s","--simulate",
        help="Simulate random user sending Satoshi to another random user. Input: int - rounds to run simulator")

    args = parser.parse_args()

    if args.generate:
        number = int(args.generate)
        generate_accounts(number)

    if args.simulate:
        number = int(args.simulate)
        for i in range(0, number):
            one_round()

if __name__ == "__main__":
  main(sys.argv[1:])