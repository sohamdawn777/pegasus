import time
import heapq
import threading
from backend.utils.helpers import QueueHelper
from backend.detection.config import stabilityThresholds
from backend.detection.sharedState import fileDict, heap, cond
import backend.detection.sharedState as shared

class Scheduler(threading.Thread):
    def __init__(self, fileQueue, testFolder, snapFolder, dbQueue):
        super().__init__()
        self.fileQueue= fileQueue
        self.dbQueue= dbQueue
        self.snapFolder= snapFolder
        self.testFolder= testFolder
        self.schedulerEvent= threading.Event()
    def run(self):
        while not self.schedulerEvent.is_set():
            oldest= None
            candidate= None
            with cond:
                while (not heap or shared.state=="CRITICAL") and not self.schedulerEvent.is_set():
                    cond.wait()
                while heap:
                    oldest= heap[0]
                    if oldest[1] in fileDict.keys() and oldest[0]<=fileDict[oldest[1]]["last_modified"]+stabilityThresholds["event_threshold"]:
                        break
                    else:
                        heapq.heappop(heap)
                        continue
                if not heap:
                    continue
                
            rem= oldest[0]-time.monotonic()
            if rem>0:
                time.sleep(rem)
            else:
                with cond:
                    if oldest[1] in fileDict.keys() and oldest[0]<=fileDict[oldest[1]]["last_modified"]+stabilityThresholds["event_threshold"]:
                        candidate= heapq.heappop(heap)

            if candidate==None or shared.state=="CRITICAL": 
                continue 
            helperResp= QueueHelper.helper(self.fileQueue, {"operation": candidate[2], "params": (candidate[1], False, None, None, None, False, self.snapFolder)}, 3)
        return