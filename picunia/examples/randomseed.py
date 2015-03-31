import urllib2

# True random number from random.org. The randomness is based on
# atmospheric noise.
class RandomSeed():
    @staticmethod
    def generate(keybits=256):
        b = keybits / 8
        url = 'https://www.random.org/cgi-bin/randbyte?nbytes=%d&format=b' % b
        response = urllib2.urlopen(url)
        html = response.read()
        html = html.replace('\n', '').replace(' ', '')
        privateKey = int(html, 2)
        return privateKey
