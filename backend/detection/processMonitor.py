import os
import time
import psutil
import threading
import backend.detection.sharedState as shared
from backend.detection.sharedState import cond
from backend.utils.helpers import Containment
from backend.detection.sharedState import criticalState, restoreState, gcsState

class ProcessMonitor(threading.Thread):
    def __init__(self, testFolder, projectRoot):
        super().__init__()
        self.processEvent= threading.Event()
        self.testFolder= os.path.realpath(testFolder)
        self.projectRoot= os.path.realpath(projectRoot)
    def run(self):
        while not self.processEvent.is_set():
            criticalState.wait()
            with cond:
                state= shared.state
            if state=="CRITICAL":
                attPid= None
                createdTime= None
                found= False
                iter= psutil.process_iter(attrs= ['pid', 'name'])
                for i in iter:
                    try:
                        proc= psutil.Process(i.pid)
                        fileDescriptors= proc.open_files()
                        for j in fileDescriptors:
                            if os.path.realpath(j.path).startswith(self.testFolder+os.sep) and i.pid!=os.getpid():
                                attPid= i.pid
                                createdTime= proc.create_time()
                                found= True
                                break
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        continue
                    if found:
                        break
                    else:
                        try:
                            if os.path.realpath(proc.cwd()).startswith(self.testFolder+os.sep) and i.pid!=os.getpid():
                                attPid= i.pid
                                createdTime= proc.create_time()
                                break
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            continue
                        try:
                            found_cmd= False
                            for s in proc.cmdline():
                                if os.path.realpath(s).startswith(self.testFolder+os.sep) and i.pid!=os.getpid():
                                    attPid= i.pid
                                    createdTime= proc.create_time()
                                    found_cmd= True
                                    break
                            if found_cmd:
                                break
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            continue
                        try:
                            if os.path.realpath(proc.exe()).startswith(self.projectRoot+os.sep) and i.pid!=os.getpid():
                                attPid= i.pid
                                createdTime= proc.create_time()
                                break
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            continue
                
                if attPid==None and createdTime==None:
                    Containment.helper(self.testFolder)
                    print("[WARNING] FOLDER LOCKED...")
                    with cond:
                        shared.state= "WARNING"
                    print(f"[INFO] SYSTEM STATE: {shared.state}")
                    restoreState.set()
                    gcsState.set()
                    criticalState.clear()
                    continue
                
                try:
                    attProc= psutil.Process(attPid)
                    attProc.terminate()
                    time.sleep(0.5)
                    if psutil.pid_exists(attPid) and createdTime==attProc.create_time():
                        attProc.kill()
                    with cond:
                        shared.state= "WARNING"
                    restoreState.set()
                    gcsState.set()
                    criticalState.clear()
                    print("PROCESS KILLED...")
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    Containment.helper(self.testFolder)
                    print("FOLDER LOCKED...")
                    print("An exception occured.")
                    with cond:
                        shared.state= "WARNING"
                    restoreState.set()
                    gcsState.set()
                    criticalState.clear()
        return