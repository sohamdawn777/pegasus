import os
import uuid
import time
from backend.utils import hasher

def storeFile(filePath, isDel, delAt, safeAt, finalAt, isAtt, snapFolder):
    with open(filePath, "rb") as f:
        data= f.read()
    snapId= uuid.uuid4()

    path= os.path.join(snapFolder, str(snapId)+".snapshot")
    with open(path, "wb") as f:
        f.write(data)

    hashValue= hasher.hasher(data)
    timestamp= time.time()
    return (str(snapId), filePath, hashValue, isDel, delAt, safeAt, finalAt, isAtt, timestamp)

def deleteFile(snapId, snapFolder):
    path= os.path.join(snapFolder, str(snapId)+".snapshot")
    try:
        os.remove(path)
    except Exception:
        print("Error deleting...")
    return (time.time(), snapId)