from pycoin.tx import TxOut
from pycoin.tx.pay_to import ScriptNulldata


MAX_MESSAGE_SIZE=40

class ProofOfExistence():
	def __init__(self, contract):
		self.contract = contract
		self.amount = 0
		self.transaction_out = []

	def generate_txout(self):
		chunks_40_bytes = [self.contract[i:i+MAX_MESSAGE_SIZE] 
							for i in range(0, len(self.contract), MAX_MESSAGE_SIZE)]

		for chunk in chunks_40_bytes:
			if len(chunk) < 5:#chunk cannot be less than 5 char, append space so it becomes 5
				delta = 5 - len(chunk)
				chunk = (chunk+delta*' ')

			script = ScriptNulldata(chunk).script()
			self.transaction_out.append(TxOut(self.amount, script))

		return self.transaction_out

'''
contract="radde is the coolest person in the world. Everyone knows this fact"
contract += "Wise busy past both park when an ye no. Nay likely her length sooner thrown sex lively income. The"
contract += "Extremity direction existence as dashwoods do up. Securing marianne led welcomed offended but offering six raptures. Conveying concluded newspaper rapturous oh at. Two indeed suffer saw beyond far former mrs remain. Occasional continuing possession we insensible an sentiments as is. Law but reasonably motionless principles she. Has six worse downs far blush rooms above stood. Remain lively hardly needed at do by. Two you fat downs fanny three. True mr gone most at. Dare as name just when with it body. Travelling inquietude she increasing off impossible the. Cottage be noisier looking to we promise on. Disposal to kindness appetite diverted learning of on raptures. Betrayed any may returned now dashwood formerly. Balls way delay shy boy man views. No so instrument discretion unsatiable to in. Excited him now natural saw passage offices you minuter. At by asked being court hopes. Farther so friends am to detract. Forbade concern do private be. Offending residence but men engrossed shy. Pretend am earnest offered arrived company so on. Felicity informed yet had admitted strictly how you. To sure calm much most long me mean. Able rent long in do we. Uncommonly no it announcing melancholy an in. Mirth learn it he given. Secure shy favour length all twenty denote. He felicity no an at packages answered opinions juvenile. Surprise steepest recurred landlord mr wandered amounted of. Continuing devonshire but considered its. Rose past oh shew roof is song neat. Do depend better praise do friend garden an wonder to. Intention age nay otherwise but breakfast. Around garden beyond to extent by. Paid was hill sir high. For him precaution any advantages dissimilar comparison few terminated projecting. Prevailed discovery immediate objection of ye at. Repair summer one winter living feebly pretty his. In so sense am known these since. Shortly respect ask cousins brought add tedious nay. Expect relied do we genius is. On as around spirit of hearts genius. Is raptures daughter branched laughter peculiar in settling. Sense child do state to defer mr of forty. Become latter but nor abroad wisdom waited. Was delivered gentleman acuteness but daughters. In as of whole as match asked. Pleasure exertion put add entrance distance drawings. In equally matters showing greatly it as. Want name any wise are able park when. Saw vicinity judgment remember finished men throwing. Improved own provided blessing may peculiar domestic. Sight house has sex never. No visited raising gravity outward subject my cottage mr be. Hold do at tore in park feet near my case. Invitation at understood occasional sentiments insipidity inhabiting in. Off melancholy alteration principles old. Is do speedily kindness properly oh. Respect article painted cottage he is offices parlors"

c = ProofOfExistence(contract)

c.generate_txout()
'''