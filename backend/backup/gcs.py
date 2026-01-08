import os
import time
import queue
import base64
import threading
from backend.detection.config import restore_threshold
from dotenv import load_dotenv
from google.cloud import storage
from google.api_core.exceptions import TooManyRequests
from backend.utils.helpers import QueueHelper
from backend.storage.dbThread import dbOps
from backend.detection.sharedState import gcsState
from cryptography.fernet import Fernet
from argon2.low_level import hash_secret_raw, Type

class EncBackup(threading.Thread):
    def __init__(self, dbQueue, testFolder, restoreFolder, snapFolder, passKey, salt):
        super().__init__()
        load_dotenv()
        self.testFolder= testFolder
        self.restoreFolder= restoreFolder
        self.snapFolder= snapFolder
        self.dbQueue= dbQueue
        self.resp= queue.Queue(maxsize= 100)
        self.gcsEvent= threading.Event()
        self.key= base64.urlsafe_b64encode(hash_secret_raw(secret= passKey.encode('utf-8'), salt= salt, time_cost= 3, memory_cost= 65536, parallelism= 2, hash_len= 32, type= Type.ID))
        self.encObj= Fernet(self.key)

    def run(self):
        client= storage.Client()
        bucket= client.bucket(os.environ["CLIENT_BUCKET"])

        while not self.gcsEvent.is_set():
            gcsState.wait()
            response= None
            curTime= time.time()
            query= QueueHelper.helper(self.dbQueue, {"operation": dbOps["fetch_safe_hashes"], "params": (False, False, curTime-restore_threshold), "resp": self.resp}, 3)
            if query:
                try:
                    response= self.resp.get(block= True, timeout= 1)
                except queue.Empty:
                    continue
                if response!=None:
                    tempDir= os.path.join(self.restoreFolder, "temp")
                    os.makedirs(tempDir, exist_ok= True)
                    for i in response:
                        relPath= os.path.relpath(os.path.dirname(i[2]), self.testFolder)
                        blobPath= os.path.join(relPath, os.path.basename(i[2])).replace(os.sep, "/")
                        try:
                            blob= bucket.blob(blobPath)
                        except TooManyRequests:
                            time.sleep(0.5)
                            blob= bucket.blob(blobPath)
                        try:
                            with open(os.path.join(self.snapFolder, i[1]+".snapshot"), "rb") as f:
                                data= f.read()
                        except FileNotFoundError:
                            continue
                        dataEnc= self.encObj.encrypt(data)
                        tempPath= os.path.join(tempDir, f"{i[1]}.enc")
                        with open(tempPath, "wb") as f:
                            f.write(dataEnc)
                        try:
                            blob.upload_from_filename(tempPath, content_type= "application/octet-stream") 
                        except TooManyRequests:
                            time.sleep(0.5)
                            blob.upload_from_filename(tempPath, content_type= "application/octet-stream") 
                        os.remove(tempPath)
                    if os.path.exists(tempDir) and not os.listdir(tempDir):
                        os.rmdir(tempDir)
                    print("[INFO] UPLOADED DATA TO GOOGLE CLOUD STORAGE SAFELY...")
            gcsState.clear() 
        return 