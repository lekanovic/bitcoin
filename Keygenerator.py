import hashlib
import urllib2


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

    def __init__(self):
        self.url = 'https://www.random.org/cgi-bin/randbyte?nbytes=32&format=b'
        response = urllib2.urlopen(self.url)
        html = response.read()
        html = html.replace('\n','').replace(' ','')
        self.privateKey = int(html,2)

        ec = ElipticCurve()
        self.publicKey = ec.EccMultiply(self.privateKey)
        self.publicKey = "04" + "%064x" % self.publicKey[0] + "%064x" % self.publicKey[1];
        self.alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

    def base58encode(self, n):
        result = ''
        while n > 0:
            result = self.alphabet[n%58] + result
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

    def getPrivkeyWIF(self):
        #Add 0x80 byte to the front
        privKeyWIF = "80%x" % self.privateKey
        tmp = privKeyWIF

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

    def getPubAddress(self):
        #SHA-256
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


a = KeyManager()

WIF = a.getPrivkeyWIF()
print "Privkey: %s" % a.getPrivkey()
print "Pubkey:  %s" % a.getPubkey()
print "PrivateKeyWIF: %s" % a.getPrivkeyWIF()
print "BitcoinPublicAddress: %s" % a.getPubAddress()
print "Check if WIF is valid: %s" % a.WIFCheckSum(WIF)

