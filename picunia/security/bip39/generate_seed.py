from pycoin.key.BIP32Node import BIP32Node
from picunia.config.settings import Settings
from mnemonic import Mnemonic
import os
import stat


'''
	This module will generate a seed based on the BIP39 standard.
	It will write the mnemonics to a file and make the file read-only.
	It will also make the file immutable so it cannot be deleted by
	misstake.
'''
# Generate seed using BIP39
def BIP39_seed():
    mnemo = Mnemonic('english')
    words = mnemo.generate(512)

    if not mnemo.check(words):
        print "Something went wrong"
        exit(1)

    seed = Mnemonic.to_seed(words)

    return seed, words

def make_file_immutable():
	os.chmod(Settings.SEED_FILE,
			 stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

	cmd = "sudo chattr +i %s" % Settings.SEED_FILE
	os.system(cmd)

def main():
	seed, word = BIP39_seed()

	if os.path.isfile(Settings.SEED_FILE):
		print "File %s already exists, cannot overwrite!!" % Settings.SEED_FILE
		exit(1)

	print word

	with open(Settings.SEED_FILE,'w') as f:
		f.write(word)
		f.close()

	make_file_immutable()

if __name__ == "__main__":
	main()
