import queue
import threading
import time
from backend.utils.helpers import QueueHelper
from backend.files import fileOps
from backend.storage.dbThread import dbOps
import backend.detection.sharedState as shared
from backend.detection.sharedState import cond

fileOps= {
    "file_store": fileOps.storeFile,
    "file_delete": fileOps.deleteFile
}

class FileThread(threading.Thread):
    def __init__(self, dbQueue):
        super().__init__()
        self.dbQueue= dbQueue
        self.fileQueue= queue.Queue(maxsize= 100)
        self.fileEvent= threading.Event()

    def createSnapshot(self, taskObj):
        result= fileOps["file_store"](*taskObj["params"])
        with cond:
            state= shared.state
        if state=="SAFE":
            helperRespWrite= QueueHelper.helper(self.dbQueue, {"operation": dbOps["store_hashes"], "params": (result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7], result[8]), "resp": None}, 3)
        elif state=="WARNING":
            helperRespWrite= QueueHelper.helper(self.dbQueue, {"operation": dbOps["store_hashes"], "params": (result[0], result[1], result[2], result[3], result[4], result[5], result[6], True, result[8]), "resp": None}, 3)
        else:
            helperRespWrite= False

    def deleteSnapshot(self, taskObj):
        result= fileOps["file_delete"](*taskObj["params"])
        helperRespDel= QueueHelper.helper(self.dbQueue, {"operation": dbOps["remove_hashes"], "params": (result[0], result[1]),"resp": None}, 3)
    def run(self):
        while not self.fileEvent.is_set():
            with cond:
                state= shared.state
            if state=="CRITICAL":
                time.sleep(1)
                continue                
            else:
                try:
                    taskObj= self.fileQueue.get(block= True, timeout= 1)
                    if taskObj["operation"] in ("file_store", "file_modify"):
                        self.createSnapshot(taskObj)
                    else:
                        self.deleteSnapshot(taskObj)
                except queue.Empty:
                    time.sleep(0.5)
                    continue
        return