import time
import queue
import threading
from backend.storage.dbThread import dbOps
from backend.utils.helpers import QueueHelper
import backend.detection.sharedState as shared
from backend.detection.sharedState import cond

class FileAuditor(threading.Thread):
    def __init__(self, snapFolder, fileQueue, dbQueue):
        super().__init__()
        self.fileAuditEvent= threading.Event()
        self.snapFolder= snapFolder
        self.fileQueue= fileQueue
        self.dbQueue= dbQueue
        self.resp= queue.Queue(maxsize= 100)
        self.last_run= 0
        self.interval= 60
    def run(self):
        while not self.fileAuditEvent.is_set():
            now= time.monotonic()
            if now-self.last_run>=self.interval:
                with cond:
                    state= shared.state
                if state=="CRITICAL":
                    self.last_run= now
                    time.sleep(1)
                    continue

                response= None
                query= QueueHelper.helper(self.dbQueue, {"operation": dbOps["fetch_hashes"], "params": (True, time.time()), "resp": self.resp}, 3)
                if query:
                    try:
                        response= self.resp.get(block= True, timeout= 1)
                    except queue.Empty:
                        continue
                    if response!=None:
                        if len(response)!=0:
                            for i in response:
                                helperResp= QueueHelper.helper(self.fileQueue, {"operation": "file_delete", "params": (i[1], self.snapFolder)}, 3)
            time.sleep(1)
        return