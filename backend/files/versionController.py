import time
import threading
from backend.storage.dbThread import dbOps
from backend.utils.helpers import QueueHelper
from backend.detection.config import auditThresholds
import backend.detection.sharedState as shared
from backend.detection.sharedState import cond

class VersionController(threading.Thread):
    def __init__(self, snapFolder, dbQueue):
        super().__init__()
        self.versionControlEvent= threading.Event()
        self.snapFolder= snapFolder
        self.dbQueue= dbQueue
        self.last_run= 0
        self.interval= 60
    def run(self):
        while not self.versionControlEvent.is_set():
            now= time.monotonic()
            if now-self.last_run>=self.interval:
                with cond:
                    state= shared.state
                if state=="CRITICAL":
                    self.last_run= now
                    time.sleep(1)
                    continue

                helperResp= QueueHelper.helper(self.dbQueue, {"operation": dbOps["update_file_stat_del2"], "params": (True, time.time(), time.time()+auditThresholds["delete_scheduling"], None), "resp": None}, 3)
                self.last_run= now
            time.sleep(1)
        return