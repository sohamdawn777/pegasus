import os
import time
import heapq
from backend.utils.helpers import QueueHelper
from backend.storage.dbThread import dbOps
from watchdog.events import FileSystemEventHandler
from backend.detection.sharedState import fileDict, heap, cond
from backend.detection.config import stabilityThresholds, auditThresholds

class EventHandler(FileSystemEventHandler):
    def __init__(self, testFolder, snapFolder, dbQueue, fileQueue):
        super().__init__()
        print("[INFO] MONITORING ACTIVE...")
        self.testFolder= testFolder
        self.snapFolder= snapFolder
        self.dbQueue= dbQueue
        self.fileQueue= fileQueue
    def on_created(self, event):
        if event.is_directory:
            return
        print("[INFO] OBSERVED FILE SYSTEM EVENT: CREATE...")
        with cond:
            fileDict[event.src_path]= {"last_modified": time.monotonic(), "on_modified_count": 1, "deltas": [], "entropy": None, "ext_changed": False, "old_ext": os.path.splitext(event.src_path)[1].lower().lstrip("."), "new_ext": os.path.splitext(event.src_path)[1].lower().lstrip("."), "last_rename_time": None, "rename_count": 0, "directory": os.path.dirname(event.src_path)}
            heapq.heappush(heap, (fileDict[event.src_path]["last_modified"]+stabilityThresholds["event_threshold"], event.src_path, "file_store"))
            cond.notify_all()
    def on_modified(self, event):
        if event.is_directory:
            return
        print("[INFO] OBSERVED FILE SYSTEM EVENT: MODIFY...")
        if event.src_path not in fileDict:
            with cond:
                fileDict[event.src_path]= {"last_modified": time.monotonic(), "on_modified_count": 1, "deltas": [], "entropy": None, "ext_changed": False, "old_ext": os.path.splitext(event.src_path)[1].lower().lstrip("."), "new_ext": os.path.splitext(event.src_path)[1].lower().lstrip("."), "last_rename_time": None, "rename_count": 0, "directory": os.path.dirname(event.src_path)}
                heapq.heappush(heap, (fileDict[event.src_path]["last_modified"]+stabilityThresholds["event_threshold"], event.src_path, "file_modify"))
                cond.notify_all()
        else:
            t= time.monotonic()
            with cond:
                fileDict[event.src_path]["deltas"].append(t-fileDict[event.src_path]["last_modified"])
                fileDict[event.src_path]["last_modified"]= t
                fileDict[event.src_path]["on_modified_count"]+=1
                heapq.heappush(heap, (fileDict[event.src_path]["last_modified"]+stabilityThresholds["event_threshold"], event.src_path, "file_modify"))
                cond.notify_all()
    def on_moved(self, event):
        if event.is_directory: 
            return
        print("[INFO] OBSERVED FILE SYSTEM EVENT: RENAME...")
        helperResp= QueueHelper.helper(self.dbQueue, {"operation": dbOps["update_file_paths"], "params": (event.src_path, event.dest_path), "resp": None}, 3)
        if helperResp==True:
            with cond:
                fileDict[event.dest_path]= fileDict[event.src_path]
                del fileDict[event.src_path]
                fileDict[event.dest_path]["directory"]= os.path.dirname(event.dest_path)

                if os.path.splitext(event.dest_path)[1].lower().lstrip(".")==os.path.splitext(event.src_path)[1].lower().lstrip("."):
                    pass
                else:
                    fileDict[event.dest_path]["ext_changed"]= True
                    fileDict[event.dest_path]["old_ext"]= os.path.splitext(event.src_path)[1].lower().lstrip(".")
                    fileDict[event.dest_path]["new_ext"]= os.path.splitext(event.dest_path)[1].lower().lstrip(".")
                    fileDict[event.dest_path]["last_rename_time"]= time.monotonic()
                    fileDict[event.dest_path]["rename_count"]+=1
                heapq.heappush(heap, (fileDict[event.dest_path]["last_modified"]+stabilityThresholds["event_threshold"], event.dest_path, "file_modify"))
                cond.notify_all()
        else:
            pass    
    def on_deleted(self, event):
        if event.is_directory:
            return
        print("[INFO] OBSERVED FILE SYSTEM EVENT: DELETE...")
        helperResp= QueueHelper.helper(self.dbQueue, {"operation": dbOps["update_file_stat_del1"], "params": (event.src_path, True, time.time(), time.time()+auditThresholds["delete_scheduling"], None), "resp": None}, 3)
        if helperResp==True:
            with cond:
                del fileDict[event.src_path]
                cond.notify_all()
        else:
            pass