# Super simple Elliptic Curve Presentation. No imported libraries, wrappers, nothing.
# For educational purposes only

# Below are the public specs for Bitcoin's curve - the secp256k1

import hashlib
import base58

Pcurve = 2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 -1 # The proven prime
N=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141 # Number of points in the field
Acurve = 0; Bcurve = 7 # These two defines the elliptic curve. y^2 = x^3 + Acurve * x + Bcurve
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
GPoint = (Gx,Gy) # This is our generator point. Trillions of dif ones possible

#Individual Transaction/Personal Information
privKey = 0x18E14A7B6A307F426A94F8114701E7C8E774E7F9A47E2C2035DB29A206321725 #replace with any private key

def modinv(a,n=Pcurve): #Extended Euclidean Algorithm/'division' in elliptic curves
    lm, hm = 1,0
    low, high = a%n,n
    while low > 1:
        ratio = high/low
        nm, new = hm-lm*ratio, high-low*ratio
        lm, low, hm, high = nm, new, lm, low
    return lm % n

def ECadd(a,b): # Not true addition, invented for EC. Could have been called anything.
    LamAdd = ((b[1]-a[1]) * modinv(b[0]-a[0],Pcurve)) % Pcurve
    x = (LamAdd*LamAdd-a[0]-b[0]) % Pcurve
    y = (LamAdd*(a[0]-x)-a[1]) % Pcurve
    return (x,y)

def ECdouble(a): # This is called point doubling, also invented for EC.
    Lam = ((3*a[0]*a[0]+Acurve) * modinv((2*a[1]),Pcurve)) % Pcurve
    x = (Lam*Lam-2*a[0]) % Pcurve
    y = (Lam*(a[0]-x)-a[1]) % Pcurve
    return (x,y)

def EccMultiply(GenPoint,ScalarHex): #Double & add. Not true multiplication
    if ScalarHex == 0 or ScalarHex >= N: raise Exception("Invalid Scalar/Private Key")
    ScalarBin = str(bin(ScalarHex))[2:]
    Q=GenPoint
    for i in range (1, len(ScalarBin)): # This is invented EC multiplication.
        Q=ECdouble(Q); # print "DUB", Q[0]; print
        if ScalarBin[i] == "1":
            Q=ECadd(Q,GenPoint); # print "ADD", Q[0]; print
    return (Q)


PublicKey = EccMultiply(GPoint,privKey)
PublicKeyHex = "04" + "%064x" % PublicKey[0] + "%064x" % PublicKey[1];

print ""
print ""
print "RADDE **************"

print "Privkey: %x" % privKey
print "Pubkey:  %s" % PublicKeyHex
print ""

#SHA-256
PublicKeyHex = PublicKeyHex.decode('hex')
publicECDSA = hashlib.sha256(PublicKeyHex).digest()
publicECDSA = publicECDSA.encode('hex_codec')
print publicECDSA

#RIPEMD-160
ripemd160 = hashlib.new('ripemd160')
ripemd160.update(hashlib.sha256(PublicKeyHex).digest())
ripmed160 = ripemd160.hexdigest()
print ripmed160

#Add version byte in front of RIPEMD-160 hash (0x00 for Main Network)
ripmed160 = "00" + ripmed160
tmp = ripmed160
print ripmed160

#Perform SHA-256 hash on the extended RIPEMD-160 result
ripmed160 = ripmed160.decode('hex')
ripmed160 = hashlib.sha256(ripmed160).digest()
ripmed160 = ripmed160.encode('hex_codec')
print ripmed160

# Perform SHA-256 hash on the result of the previous SHA-256 hash
ripmed160 = ripmed160.decode('hex')
ripmed160 = hashlib.sha256(ripmed160).digest()
ripmed160 = ripmed160.encode('hex_codec')
print ripmed160

#Take the first 4 bytes of the second SHA-256 hash. This is the address checksum
chunk = ripmed160[:8]
print chunk

#Add the 4 checksum bytes from stage 7 at the end of extended RIPEMD-160 hash from stage 4
BTCaddr = tmp + chunk
print BTCaddr

#Base58 encoding of 8
unencoded_string = str(bytearray.fromhex(BTCaddr))
BTCpublicAddr = base58.b58encode(unencoded_string)
print BTCpublicAddr

