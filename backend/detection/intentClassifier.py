import time
import threading
from backend.detection.detector import Detector
from backend.detection.config import timeWindows, deEscalationThreshold
from backend.detection.sharedState import cond, fileDict
import backend.detection.sharedState as shared
from backend.utils.helpers import EntropyCalc, Sampler

class IntentClassifier(threading.Thread):
    def __init__(self, testFolder):
        super().__init__()
        self.intentEvent= threading.Event()
        self.testFolder= testFolder
        self.cycleCount= 0
        self.stateNotSafe= False
    def run(self):
        while not self.intentEvent.is_set():
            with cond:
                while (not fileDict or shared.state=="CRITICAL") and not self.intentEvent.is_set():
                    cond.wait()
                fileDictCopyI= {k: v.copy() for k, v in fileDict.items()}
            
            for i in fileDictCopyI:
                try:
                    with open(i, "rb") as f:
                        data= Sampler.helper(f)
                        fileDictCopyI[i]["entropy"]= EntropyCalc.helper(data)
                except (OSError, IOError):
                    continue
            time.sleep(timeWindows["signalWindow"])

            with cond:
                fileDictCopyF= {k: v.copy() for k, v in fileDict.items()}   
        
            detectorInst= Detector(fileDictCopyI, fileDictCopyF, self.testFolder)
            resp= detectorInst.dictInitialization()
            
            if resp:
                detectorInst.onModifiedCount()
                detectorInst.interEventTime()
                detectorInst.entropySpike()

                dirDict= detectorInst.multiFileCorrelation()

                for j in dirDict:
                    if dirDict[j]>=5:
                        print("SYSTEM IS CRITICAL")
                        with cond:
                            shared.state= "CRITICAL"
                            shared.criticalState.set()
                        break
                    elif dirDict[j]>=3 and dirDict[j]<5:
                        with cond:
                            if shared.state!="CRITICAL":
                                shared.state= "WARNING"
                        self.stateNotSafe= True
                with cond:
                    state= shared.state

                if state!="CRITICAL":
                    if not self.stateNotSafe:
                        self.cycleCount+=1
                    else:
                        self.cycleCount= 0
                    self.stateNotSafe= False

                    if self.cycleCount>=deEscalationThreshold and shared.state=="WARNING":
                        with cond:
                            shared.state= "SAFE"
                        self.cycleCount= 0
                        print(f"[INFO] SYSTEM STATE: {shared.state}")                  
                    else:
                        continue