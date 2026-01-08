import os
import time
import heapq
from backend.utils.helpers import QueueHelper
from backend.detection.sharedState import cond, fileDict, heap
from backend.detection.config import stabilityThresholds

class Snapshots: 
    def __init__(self, snapFolder, fileQueue):
        self.snapFolder= snapFolder
        self.fileQueue= fileQueue
    def backup(self, directory):
        fileIterator= os.walk(directory)
        for i in fileIterator:
            for j in i[2]:
                with cond:
                    fileDict[os.path.join(i[0], j)]= {"last_modified": time.monotonic(), "on_modified_count": 1, "deltas": [], "entropy": None, "ext_changed": False, "old_ext": os.path.splitext(os.path.join(i[0], j))[1].lower().lstrip("."), "new_ext": os.path.splitext(os.path.join(i[0], j))[1].lower().lstrip("."), "last_rename_time": None, "rename_count": 0, "directory": os.path.dirname(os.path.join(i[0], j))}
                    heapq.heappush(heap, (fileDict[os.path.join(i[0], j)]["last_modified"]+stabilityThresholds["event_threshold"], os.path.join(i[0], j), "file_store"))
                    cond.notify_all()
                continue
        return True