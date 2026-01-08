import time
from backend.utils.helpers import EntropyCalc, Sampler, AsciiRatio
from backend.detection.config import classificationThresholds, magicBytes, entropyDeltaThresholds, asciiRatios

class Detector:
    def __init__(self, fileDictCopyI, fileDictCopyF, testFolder):
        self.fileDictCopyI= fileDictCopyI
        self.fileDictCopyF= fileDictCopyF
        self.intentDict= {}
        self.dirDict= {}
        self.testFolder= testFolder

    def dictInitialization(self):
        for i in self.fileDictCopyF:
            self.intentDict.setdefault(i, 0)
            self.dirDict.setdefault(self.fileDictCopyF[i]["directory"], 0)
        return True
    
    
    def onModifiedCount(self):
        for i in self.fileDictCopyF:
            if i in self.fileDictCopyI:
                if self.fileDictCopyF[i]["on_modified_count"]-self.fileDictCopyI[i]["on_modified_count"]<=classificationThresholds["on_modified_threshold"]["SAFE"]:
                    pass
                elif self.fileDictCopyF[i]["on_modified_count"]-self.fileDictCopyI[i]["on_modified_count"]<=classificationThresholds["on_modified_threshold"]["CRITICAL"]:
                    self.intentDict[i]+=1
                else:
                    self.intentDict[i]+=2
            elif i not in self.fileDictCopyI and self.fileDictCopyF[i]["last_rename_time"]!=None:
                now= time.monotonic()
                if now-self.fileDictCopyF[i]["last_rename_time"]<=1 and self.fileDictCopyF[i]["on_modified_count"]>=5:
                    self.intentDict[i]+=2
                elif now-self.fileDictCopyF[i]["last_rename_time"]<=1 or self.fileDictCopyF[i]["on_modified_count"]>=5:
                    self.intentDict[i]+=1
                else:
                    pass
    
    def interEventTime(self):
        for i in self.fileDictCopyF:
            if len(self.fileDictCopyF[i]["deltas"])>=5:
                count= sum(1 for x in self.fileDictCopyF[i]["deltas"] if x<=classificationThresholds["deltas"]["CRITICAL"])
                if count/len(self.fileDictCopyF[i]["deltas"])<=classificationThresholds["ratios"]["SAFE"]:
                    pass
                elif count/len(self.fileDictCopyF[i]["deltas"])<classificationThresholds["ratios"]["CRITICAL"]:
                    self.intentDict[i]+=1
                else:
                    self.intentDict[i]+=2
    
    def entropySpike(self):
        now= time.monotonic()
        for i in self.fileDictCopyF:
                found= False
                try:
                    with open(i, "rb") as f:
                        magicNo= f.read(16)
                        f.seek(0, 0)
                        data= Sampler.helper(f)
                        entropy= EntropyCalc.helper(data)
                        if i in self.fileDictCopyI:
                            delta= abs(entropy-self.fileDictCopyI[i]["entropy"])

                            for j in magicBytes:
                                if magicBytes[j]["magic"]==magicNo[:len(magicBytes[j]["magic"])]:
                                        if delta>=entropyDeltaThresholds[magicBytes[j]["entropyClass"]]:
                                            self.intentDict[i]+=2
                                        elif delta<entropyDeltaThresholds[magicBytes[j]["entropyClass"]] and delta>=0.5*entropyDeltaThresholds[magicBytes[j]["entropyClass"]]:
                                            self.intentDict[i]+=1
                                        else:
                                            pass
                                        found= True
                                        break
                            if not found:
                                asciiRatio= AsciiRatio.helper(data)
                                if asciiRatio>=asciiRatios["text-like"]:
                                    if delta>=entropyDeltaThresholds["low"]:
                                        self.intentDict[i]+=2
                                    elif delta<entropyDeltaThresholds["low"] and delta>=0.5*entropyDeltaThresholds["low"]:
                                        self.intentDict[i]+=1
                                    else:
                                        pass
                                else:
                                    if delta>=entropyDeltaThresholds["unknown"]:
                                        self.intentDict[i]+=2
                                    elif delta<entropyDeltaThresholds["unknown"] and delta>=0.5*entropyDeltaThresholds["unknown"]:
                                        self.intentDict[i]+=1
                                    else:
                                        pass
                        elif i not in self.fileDictCopyI and self.fileDictCopyF[i]["last_rename_time"]!=None:
                            if now-self.fileDictCopyF[i]["last_rename_time"]<=1 and entropy>=7.2:
                                self.intentDict[i]+=2
                            elif now-self.fileDictCopyF[i]["last_rename_time"]<=1 or entropy>=7.2:
                                self.intentDict[i]+=1
                            else:
                                pass
                except (OSError, IOError):
                    continue
    
    def multiFileCorrelation(self):
        for i in self.intentDict:
            if self.intentDict[i]>=3:
                self.dirDict[self.fileDictCopyF[i]["directory"]]+=1
        return self.dirDict