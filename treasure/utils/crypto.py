# utils/crypto.py
from nacl import pwhash, secret, utils
from nacl.exceptions import CryptoError

from .constants import KEY_SIZE, MEM_LIMIT, OPS_LIMIT, SALT_SIZE
from .data import to_bytes  # Assuming to_bytes remains useful


def derive_key(password: bytes, salt: bytes) -> bytes:
    """Derives a cryptographic key from a password and salt using Argon2id."""
    # Use Argon2id - generally preferred over Argon2i
    return pwhash.argon2id.kdf(
        KEY_SIZE, password, salt, opslimit=OPS_LIMIT, memlimit=MEM_LIMIT
    )


def encrypt(plain_text: bytes, password: str) -> bytes:
    """
    Encrypts plaintext using a password.

    Generates a unique salt, derives a key, encrypts with SecretBox,
    and returns salt + ciphertext.
    """
    password_bytes = to_bytes(password)
    # 1. Generate a unique salt for *this* encryption
    salt = utils.random(SALT_SIZE)
    # 2. Derive the key using the password and unique salt
    key = derive_key(password_bytes, salt)
    # 3. Encrypt using SecretBox (handles nonce generation internally)
    box = secret.SecretBox(key)
    ciphertext = box.encrypt(plain_text)
    # 4. Return salt prepended to the ciphertext (nonce is already part of nacl's ciphertext)
    return salt + ciphertext


def decrypt(salt_plus_ciphertext: bytes, password: str) -> bytes:
    """
    Decrypts data previously encrypted by the encrypt function.

    Extracts salt, derives key, decrypts with SecretBox.
    Raises ValueError if decryption fails (wrong password, corrupted data).
    """
    if len(salt_plus_ciphertext) < SALT_SIZE:
        raise ValueError("Ciphertext is too short to contain salt.")

    password_bytes = to_bytes(password)
    # 1. Extract the salt
    salt = salt_plus_ciphertext[:SALT_SIZE]
    # 2. Extract the actual ciphertext
    ciphertext = salt_plus_ciphertext[SALT_SIZE:]
    # 3. Derive the key using the password and the extracted salt
    key = derive_key(password_bytes, salt)
    # 4. Decrypt
    box = secret.SecretBox(key)
    try:
        plain_text = box.decrypt(ciphertext)
        return plain_text
    except CryptoError as e:
        # Catching nacl's specific error for decryption failure
        raise ValueError("Decryption failed. Wrong password or corrupted data.") from e
