from gcm import *


def send_to_device(gcm_api_key, message, reg_id):
	'''
		Send a message to a device like android or iphone.
		the message will be sent to the reg_id.
	'''
	data = {'message': message}
	reg_ids = [reg_id]

	gcm = GCM(gcm_api_key)
	response = gcm.json_request(registration_ids=reg_ids, data=data)

	if 'errors' in response:
		return False
	return True