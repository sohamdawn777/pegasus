import os
import time
import queue
import threading
from backend.utils.helpers import QueueHelper
from backend.storage.dbThread import dbOps
from backend.detection.sharedState import restoreState
from backend.detection.config import restore_threshold

class RestoreBackup(threading.Thread):
    def __init__(self, dbQueue, testFolder, snapFolder, restoreFolder):
        super().__init__()
        self.dbQueue= dbQueue
        self.resp= queue.Queue(maxsize= 100)
        self.backupEvent= threading.Event()
        self.testFolder= testFolder
        self.snapFolder= snapFolder
        self.restoreFolder= restoreFolder
    def run(self):
        while not self.backupEvent.is_set():
            restoreState.wait()
            response= None
            curTime= time.time()
            query= QueueHelper.helper(self.dbQueue, {"operation": dbOps["fetch_safe_hashes"], "params": (False, False, curTime-restore_threshold), "resp": self.resp}, 3)
            if query:
                try:
                    response= self.resp.get(block= True, timeout= 1)
                except queue.Empty:
                    continue
                if response!=None:
                    for i in response:
                        relPath= os.path.relpath(os.path.dirname(i[2]), self.testFolder)
                        restorePath= os.path.join(self.restoreFolder, relPath)
                        os.makedirs(restorePath, exist_ok= True)
                        try:
                            with open(os.path.join(self.snapFolder, i[1]+".snapshot"), "rb") as f:
                                data= f.read()
                        except FileNotFoundError:
                            continue
                        with open(os.path.join(restorePath, os.path.basename(i[2])), "wb") as f:
                            f.write(data) 
                    print("[INFO] RESTORED DATA TO LAST SAFE STATE...")
            restoreState.clear() 
        return 