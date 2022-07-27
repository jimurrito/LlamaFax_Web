try:
    from lib.Authlib import securePwd, valSecCreds
    from lib.General import makeXDigits
except:
    from Authlib import securePwd, valSecCreds
    from General import makeXDigits
from uuid import uuid4 as Uid
import logging
from time import sleep
from pymongo import MongoClient
import pymongo.errors
from datetime import datetime as DT

# New Mongo DB Class


class MongoDB:

    """Connects to Specified MongoDB"""

    def __init__(
        self,
        CollectionName: str,
        Host: str = None,
        DBName: str = None,
        Indexes: list = None,
    ) -> None:
        # if Host is Empty
        if Host:
            ConnectString = f"mongodb://{Host}:27017"
        else:
            ConnectString = "mongodb://127.0.0.1:27017"
        # If Database name is empty, set Database name to General
        if DBName is None:
            DBName = "General"
        # Element Creation
        self.Conn = MongoClient(ConnectString)
        self.Col = self.Conn[DBName][CollectionName]
        # If Index is required
        if Indexes != None:
            # force object into list, if not
            if not isinstance(Indexes, list):
                Indexes = [Indexes]
            # Sets Indexes
            for Index in Indexes:
                try:
                    self.Col.create_index(Index, unique=True)
                except:
                    pass

    def push(self, Insert: dict):
        """Pushes data to MongoDB Collection"""
        logging.debug(f"Pushing data to Database Collection: {Insert}")
        if isinstance(Insert, list):
            self.Col.insert_many(Insert)
        else:
            self.Col.insert_one(Insert)

    def pull(self, Num: int = 1) -> dict:
        """Pulls data from MongoDB Collection"""
        logging.info("Pulling data from Database Collection")
        return self.Col.find(limit=Num)

    def validate(self, Data: dict) -> bool:
        """Input document for validation, returns True if statment was already processed."""
        if self.Col.find_one(Data):
            return True
        return False

    def count(self) -> int:
        """Counts Documents in a MongoDB Collection"""
        return self.Col.count_documents({})

    def random(self, Count=1) -> dict:
        """Returns random document from a MongoDB Collection"""
        # https://stackoverflow.com/questions/2824157/how-can-i-get-a-random-record-from-mongodb
        Ag = list(self.Col.aggregate([{"$sample": {"size": Count}}]))
        if Count == 1:
            return Ag[0]
        return Ag

    def generateAlphaKey(self, Num: int = 1):
        """[USED ONLY WITH AN APLHA KEY DATABASE]"""
        # Assumes the database is already indexed for the codes
        idList = []
        while Num:
            Key = str(Uid())
            try:
                self.push({"code": f"{Key}", "use": False})
                logging.info("Key Generated, and pushed to Database.")
                idList.append(Key)
                Num -= 1
            except pymongo.errors.DuplicateKeyError:
                logging.warning("key generated waas already set, generating another.")
                pass
            except:
                raise Exception("Unknown Error Thrown from Database.")
        return idList

    def consumeAlphaKey(self, Input) -> bool:
        """[USED BY SIGNUP PAGE]
        \bInput will be the provided Alphakey. If it exists, it will be marked as used"""
        try:
            self.Col.update_one({"code": Input}, {"$set": {"use": True}})
            return True
        except:
            return False

    def generateBugRep(self, Upn, Email, Data):
        """[USED FOR BUG SUBMISSION]"""
        self.push(
            {
                "BugID#": f"BgID{makeXDigits(self.count()+1)}",
                "SubUsr": Upn,
                "SubEml": Email.lower(),
                "Time": DT.now().isoformat(),
                "State": "Open",
                "Data": Data,
            }
        )

    def generateSupport(self, Email, Topic, Data):
        """[USED FOR SUPPORT TICKET SUBMISSION]"""
        self.push(
            {
                "SrID#": f"SrID{makeXDigits(self.count()+1)}",
                "SubEml": Email.lower(),
                "Time": DT.now().isoformat(),
                "State": "Open",
                "issue": Topic,
                "Data": Data,
            }
        )


class Queue(MongoDB):
    """Interacts with a Queue-Like Collection"""

    def __init__(self, QueueName, Host=None) -> None:
        super().__init__(QueueName, Host, "Queue")
        # If Queue (Cappped Collection) not found, its created
        if QueueName not in self.Conn["Queue"].list_collection_names():
            self.Conn["Queue"].create_collection(QueueName, capped=True, size=5242880)
        # Sets Collection Element
        self.Col = self.Conn["Queue"][QueueName]

    def pull(self) -> dict:
        """Pulls Message from MongoDB Queue\n
        Data will be removed from Queue, once pulled."""
        logging.info("Pulling data from Queue")
        return self.Col.find_one_and_delete({})

    def pullSafe(self) -> dict:
        """Pulls Message from MongoDB Queue\n
        Pulls will not be removed from Queue."""
        logging.info("Safely Pulling data from Queue")
        return self.Col.find_one()

    def pop(self, message) -> dict:
        """[USED FOR RENDER SERVICE]
        \nRemoves Message from MongoDB Queue
        \nRequires pulled message to remove."""
        logging.info("Removing data from Queue")
        message.pop("render")
        return self.Col.delete_one(message)

    def threshold(self, MsgMax=100, Threshold=0.7) -> None:
        """returns if queue is not at max"""
        if self.Col.count_documents({}) < MsgMax:
            logging.info("Threshold not met.")
            return
        # Msg Queue is at Max Threshold
        # Waits until Queue is at Threshold %
        logging.info("Begining Sleep")
        while True:
            sleep(10)
            if self.Col.count_documents({}) < MsgMax * Threshold:
                logging.info("Queue fell under the defined Threshold, Ending Sleep.")
                return


class UAuth(MongoDB):
    """Interacts with an Authentication Collection, in MongoDB
    \nAutomatically Indexes attributes: Email & UPN"""

    def __init__(self, CollectionName, Host=None) -> None:
        super().__init__(CollectionName, Host, "AuthNZ", ["email", "upn"])
        self.Col = self.Conn["AuthNZ"][CollectionName]

    def addUserMan(self, Upn, Pwd, Email, Score=0) -> bool:
        try:
            self.Col.insert_one(
                {
                    "upn": f"{Upn}",
                    "pwd": f"{securePwd(Pwd)}",
                    "email": f"{Email.lower()}",
                    "score": Score,
                    "locked": False,
                    "attempts": 0,
                    "score": 0,
                }
            )
        except pymongo.errors.DuplicateKeyError:
            return False
        return True

    def addUserSS(self, Upn, Email, Pwd) -> int:
        """0 == Success, 1 == Email, 2 == Upn, 3 == Unknown"""
        # validate UPN/Email uniqueness, before creating user
        # If Upn conflicts
        if list(self.Col.find({"upn": {"$exists": "true", "$in": [f"{Upn}"]}})):
            return 1
        # If Email conflicts
        elif list(
            self.Col.find({"email": {"$exists": "true", "$in": [f"{Email.lower()}"]}})
        ):
            return 2
        # if password is < 6
        elif len(list(Pwd)) < 6:
            return 3

        try:
            self.Col.insert_one(
                {
                    "upn": f"{Upn}",
                    "pwd": f"{securePwd(Pwd)}",
                    "email": f"{Email.lower()}",
                    "locked": False,
                    "attempts": 0,
                    "score": 0,
                }
            )
        except pymongo.errors.DuplicateKeyError:
            return 4
        return 0

    def valCreds(self, Upn: str, Pwd: str) -> dict:
        # Get user object that matches email/upn provided
        UserObj = list(self.Col.find({"upn": {"$exists": "true", "$in": [f"{Upn}"]}}))
        if not UserObj:
            UserObj = list(
                self.Col.find(
                    {"email": {"$exists": "true", "$in": [f"{(Upn).lower()}"]}}
                )
            )
        if UserObj and valSecCreds(Pwd, dict(UserObj[0])["pwd"]):
            DictT = dict(UserObj[0])
            DictT.pop("pwd")
            return DictT

    # Update Current passwords to Higher lvl Encryption / SSPR :)
    def updatePwd(self, Upn, Pwd) -> bool:
        try:
            self.Col.update_one({"upn": Upn}, {"$set": {"pwd": securePwd(Pwd)}})
            return True
        except:
            return False

    def addtoScore(self, UserObj: dict, Mod=1) -> bool:
        UserObj.pop("_id")
        if self.Col.update_one(UserObj, {"$set": {"score": UserObj["score"] + Mod}}):
            return True
        return False

    def valCredsForgotPwd(self, Upn, Email) -> dict:
        """Intakes username and Email, returns userobject, without password :)"""
        # uses UPN to lookup user Object
        try:
            UserObj = dict(
                list(self.Col.find({"upn": {"$exists": "true", "$eq": Upn}}))[0]
            )
        except:
            return
        # Uses Object to validate email addresses
        if not UserObj:
            return
        elif UserObj["email"] != Email.lower():
            return
        # If val successful, return userobject, with password removed
        UserObj.pop("pwd")
        return UserObj


def main():

    UAuthDB = UAuth("userAuth", Host="10.4.18.2")
    # print(UAuthDB.addtoScore(UAuthDB.valCreds("Milk", "YourMom!!1"), -12))
    print(UAuthDB.random(1))

    # DBObj.push({"test": "value"})


if __name__ == "__main__":
    main()
