from nacl import pwhash

from treasure.utils import data, rand
from treasure.utils.constants import KEY_SIZE
from treasure.utils.file import get_salt


class Key:
    class SecurityLevel:
        LOW = {'ops': pwhash.argon2i.OPSLIMIT_INTERACTIVE,
               'mem': pwhash.argon2i.MEMLIMIT_INTERACTIVE}
        MEDIUM = {'ops': pwhash.argon2i.OPSLIMIT_MODERATE,
                  'mem': pwhash.argon2i.MEMLIMIT_MODERATE}
        HIGH = {'ops': pwhash.argon2i.OPSLIMIT_SENSITIVE,
                'mem': pwhash.argon2i.MEMLIMIT_SENSITIVE}

    def __init__(self, password=None, salt=None, securityLevel=SecurityLevel.HIGH):
        password = rand.gen_password() if password is None else password
        self.salt = rand.gen_salt() if salt is None else salt
        self.securityLevel = securityLevel
        self.value = Key.derive(password, self.salt, self.securityLevel)

    @staticmethod
    def derive(password, salt=None, securityLevel=SecurityLevel.HIGH):
        salt = rand.gen_salt() if salt is None else salt
        return pwhash.argon2i.kdf(KEY_SIZE, data.to_bytes(password), salt, securityLevel['ops'], securityLevel['mem'])
