from pwdlib import PasswordHash

ph=PasswordHash.recommended()

def hash_password(password):
    return ph.hash(password)

def verify_password(plain_password, hashed_password):
    return ph.verify(plain_password, hashed_password)