from nacl import pwhash, secret

# Size of the key derived by Argon2id, used by SecretBox
KEY_SIZE = secret.SecretBox.KEY_SIZE

# Size of the salt used by Argon2id
SALT_SIZE = pwhash.argon2id.SALTBYTES

# Default Argon2id parameters (using nacl's defaults which are reasonable)
# You can expose these via args if needed later.
OPS_LIMIT = pwhash.argon2id.OPSLIMIT_SENSITIVE
MEM_LIMIT = pwhash.argon2id.MEMLIMIT_SENSITIVE

# Used only if generating random passwords was intended (removed from main flow)
# PASSWORD_SIZE = 32
