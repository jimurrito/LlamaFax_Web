from random import random
import random
import pymongo.errors
import logging
import hashlib
from uuid import uuid4 as Uid
import string


def saltGen():
    ShLst = list(string.ascii_letters + string.digits)
    random.shuffle(ShLst)
    NewLst = []
    while len(NewLst) < 32:
        NewLst.append(random.choice(ShLst))
    return "".join(NewLst)


def securePwd(Input):
    # Generate Salt (32 digits)
    Salt = saltGen()
    # Hash Pwd with salt prepended
    Comp = hashlib.sha256((Salt + Input).encode()).hexdigest()
    # Append Salt to hash (last 32 digits)
    return Comp + Salt


def valSecCreds(Input, Control) -> bool:
    # gets Salt from last 32 digits of the Saved password
    Salt = Control[-32:]
    Comp = hashlib.sha256((Salt + Input).encode()).hexdigest()
    if Control == Comp + Salt:
        return True
    return False


def generateAlphaKey(aKeyDB, Num: int = 1):
    # Assumes the database is already indexed for the codes
    idList = []
    while Num:
        Key = str(Uid())
        try:
            aKeyDB.push({"code": f"{Key}", "use": False})
            logging.info("Key Generated, and pushed to Database.")
            idList.append(Key)
            Num -= 1
        except pymongo.errors.DuplicateKeyError:
            logging.warning("key generated waas already set, generating another.")
            pass
        except:
            raise Exception("Unknown Error Thrown from Database.")
    return idList


# # # LEGACY # # #
def hashPwd(Input: str, Salt: str = "bxPxwyWtR@XMbw5uzH2ZR%2CwMUUeW"):
    return hashlib.sha256((Salt + Input).encode()).hexdigest()


# # # LEGACY # # #


def main():
    Host = "10.4.18.2"
    KeyDbname = "userAuth"
    AuthDbname = "userAuth"
    # keyDB = Database(KeyDbname, Host=Host, Index="code")
    # AuthDB = UAuth(AuthDbname, Host=Host)

    # print(AuthDB.addUser("Test", "Password", "test@email.com", "testName"))
    # print(AuthDB.valCreds('Notelite',"YX#BCWSqesF8"))
    # print(generateAlphaKey(keyDB))

    # updatePwd('Notelite',"YX#BCWSqesF8")


if __name__ == "__main__":
    main()
