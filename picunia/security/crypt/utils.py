import bcrypt

def encrypt_password(password):
	hashed = bcrypt.hashpw(password, bcrypt.gensalt())
	return hashed


def validate_password(password, hashed):
	if bcrypt.hashpw(password, hashed) == hashed:
		return True
	else:
		return False

'''
# Example usage
hashed = encrypt_password('radovan')

print hashed

print compare_password('radovan', hashed)
'''