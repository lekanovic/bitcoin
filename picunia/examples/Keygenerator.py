import hashlib
from randomseed import RandomSeed

# Keygenerator is a deterministic wallet of Type1.
# https://en.bitcoin.it/wiki/Deterministic_wallet

class ElipticCurve():

    def __init__(self):

        self.Pcurve = 2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 -1 # The proven prime
        self.N=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141 # Number of points in the field
        self.Acurve = 0;
        self.Bcurve = 7 # These two defines the elliptic curve. y^2 = x^3 + Acurve * x + Bcurve
        self.Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
        self.Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
        self.GPoint = (self.Gx,self.Gy) # This is our generator point. Trillions of dif ones possible


    def modinv(self, a, n=2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 -1): #Extended Euclidean Algorithm/'division' in elliptic curves
        lm, hm = 1,0
        low, high = a%n,n
        while low > 1:
            ratio = high/low
            nm, new = hm-lm*ratio, high-low*ratio
            lm, low, hm, high = nm, new, lm, low
        return lm % n

    def ECadd(self, a,b): # Not true addition, invented for EC. Could have been called anything.
        LamAdd = ((b[1]-a[1]) * self.modinv(b[0]-a[0],self.Pcurve)) % self.Pcurve
        x = (LamAdd*LamAdd-a[0]-b[0]) % self.Pcurve
        y = (LamAdd*(a[0]-x)-a[1]) % self.Pcurve
        return (x,y)

    def ECdouble(self, a): # This is called point doubling, also invented for EC.
        Lam = ((3*a[0]*a[0]+self.Acurve) * self.modinv((2*a[1]),self.Pcurve)) % self.Pcurve
        x = (Lam*Lam-2*a[0]) % self.Pcurve
        y = (Lam*(a[0]-x)-a[1]) % self.Pcurve
        return (x,y)

    def EccMultiply(self, ScalarHex): #Double & add. Not true multiplication
        if ScalarHex == 0 or ScalarHex >= self.N: raise Exception("Invalid Scalar/Private Key")
        ScalarBin = str(bin(ScalarHex))[2:]
        Q=self.GPoint
        for i in range (1, len(ScalarBin)): # This is invented EC multiplication.
            Q=self.ECdouble(Q); # print "DUB", Q[0]; print
            if ScalarBin[i] == "1":
                Q=self.ECadd(Q,self.GPoint); # print "ADD", Q[0]; print
        return (Q)

class KeyManager():

    def __init__(self, k):
        self.privateKey = k

        self.runEC()
        self.n = 1

    def runEC(self):
        ec = ElipticCurve()
        self.Point = ec.EccMultiply(self.privateKey)
        self.publicKey = "04" + "%064x" % self.Point[0] + "%064x" % self.Point[1];
        self.alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

    def base58encode(self, n):
        result = ''
        while n > 0:
            result = self.alphabet[n % 58] + result
            n /= 58
        return result

    def base58decode(self, s):
        result = 0
        for i in range(0, len(s)):
            result = result * 58 + self.alphabet.index(s[i])
        return result

    def getPubkey(self):
        return self.publicKey

    def WIFCheckSum(self, privateWIF):
        if privateWIF[0] == 'K' or privateWIF[0] == 'L':
            print "Compressed not supported"
            return
        decoded = self.base58decode(privateWIF)
        tmp = "%x" % decoded
        b = str(hex(decoded))[2:-9]
        b = self.alignHex(b)
        b = b.decode('hex')
        b = hashlib.sha256(b).digest()
        b = b.encode('hex_codec')

        b = b.decode('hex')
        b = hashlib.sha256(b).digest()
        b = b.encode('hex_codec')
        b = "%x" % int(b, 16)

        return tmp.startswith('80') or tmp.startswith('ef') and b[:8] == tmp[-8:]

    def WIFtoPrivKey(self, privateWIF):
        if privateWIF[0] == 'K' or privateWIF[0] == 'L':
            print "Compressed not supported"
            return
        decoded = self.base58decode(privateWIF)
        b = str(hex(decoded))[3:-9]
        b = "%x" % int(b, 16)
        return b

    def getPrivkey(self):
        return "%x" % self.privateKey

    def getPrivkeyWIF(self, compressed=False):
        #Add 0x80 byte to the front
        if compressed:
            #Append 01 if compressed
            privKeyWIF = "80%x01" % self.privateKey
        else:
            privKeyWIF = "80%x" % self.privateKey
        tmp = privKeyWIF
        privKeyWIF = self.alignHex(privKeyWIF)

        #SHA-256 hash of 2
        privKeyWIF = privKeyWIF.decode('hex')
        privKeyWIF = hashlib.sha256(privKeyWIF).digest()
        privKeyWIF = privKeyWIF.encode('hex_codec')
        #print "Priv Key WIF %s" % privKeyWIF

        #SHA-256 hash of 3
        privKeyWIF = privKeyWIF.decode('hex')
        privKeyWIF = hashlib.sha256(privKeyWIF).digest()
        privKeyWIF = privKeyWIF.encode('hex_codec')
        #print "Priv Key WIF %s" % privKeyWIF

        #First 4 bytes of 4, this is the checksum
        chunk = privKeyWIF[:8]
        privKeyWIF = tmp + chunk
        #print "Priv Key WIF %s" % privKeyWIF

        #Base58 encoding of 6
        privKeyWIF = int(privKeyWIF, 16)
        privKeyWIF = self.base58encode(privKeyWIF)

        return privKeyWIF

    # Generate an new private key based on the current one + n
    # n is a sequense 1,2,3,..,n
    # Using this method we can recreate all the private key from
    # first one.
    def regenerate(self):
        privKey = self.getPrivkey() + str(self.n)
        if len(privKey) % 2 != 0:
            privKey = "0" + self.getPrivkey() + str(self.n)
        privKey = privKey.decode('hex')
        privKey = hashlib.sha256(privKey).digest()
        privKey = privKey.encode('hex_codec')

        self.privateKey = int(privKey, 16)
        self.runEC()
        self.n = self.n + 1

    # Make sure that the key length is even. Otherwise
    # calling string.encode('hex') will crash.
    def alignHex(self, h):
        if len(h) % 2 != 0:
            return "0%s" % h
        return h

    def getPubAddress(self, compressed=False):
        if compressed:
            p = int(str(a.Point[1])[-1:])

            if p % 2 == 0:
                p = "02%x" % a.Point[0]
            else:
                p = "03%x" % a.Point[0]

            p = self.alignHex(p)

            PublicKeyHex = p.decode('hex')
        else:
            PublicKeyHex = self.publicKey.decode('hex')

        publicECDSA = hashlib.sha256(PublicKeyHex).digest()
        publicECDSA = publicECDSA.encode('hex_codec')
        #print publicECDSA

        #RIPEMD-160
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(hashlib.sha256(PublicKeyHex).digest())
        ripmed160 = ripemd160.hexdigest()
        #print ripmed160

        #Add version byte in front of RIPEMD-160 hash (0x00 for Main Network)
        ripmed160 = "00" + ripmed160
        tmp = ripmed160
        #print ripmed160

        #Perform SHA-256 hash on the extended RIPEMD-160 result
        ripmed160 = ripmed160.decode('hex')
        ripmed160 = hashlib.sha256(ripmed160).digest()
        ripmed160 = ripmed160.encode('hex_codec')
        #print ripmed160

        # Perform SHA-256 hash on the result of the previous SHA-256 hash
        ripmed160 = ripmed160.decode('hex')
        ripmed160 = hashlib.sha256(ripmed160).digest()
        ripmed160 = ripmed160.encode('hex_codec')
        #print ripmed160

        #Take the first 4 bytes of the second SHA-256 hash. This is the address checksum
        chunk = ripmed160[:8]
        #print chunk

        #Add the 4 checksum bytes from stage 7 at the end of extended RIPEMD-160 hash from stage 4
        BTCaddr = tmp + chunk

        #Base58 encoding of 8
        BTCaddr = int(BTCaddr, 16)
        BTCpublicAddr = "1" + self.base58encode(BTCaddr)

        return BTCpublicAddr

    def toString(self):
        WIF = self.getPrivkeyWIF()
        print "-Privkey-"
        print "    %s" % self.getPrivkey()
        print "-Pubkey-"
        print "    %s" % self.getPubkey()

        print "-PrivateKeyWIF-"
        print "    Uncompressed: %s" % self.getPrivkeyWIF()
        print "    Compressed: %s" % self.getPrivkeyWIF(True)

        print "-Bitcoin Public Address-"
        print "    Uncompressed: %s" % self.getPubAddress()
        print "    Compressed: %s" % self.getPubAddress(True)

        print "WIF is valid: %s" % self.WIFCheckSum(WIF)


rootKey = RandomSeed().generate()
#rootKey = 0xe602879fbd6116309f9175ef887cdaf660a4b51c11bedb4c082e78115bcd2906
a = KeyManager(rootKey)

for i in range(0,2):
    a.toString()
    a.regenerate()
    a.toString()
    a.regenerate()
    a.toString()
