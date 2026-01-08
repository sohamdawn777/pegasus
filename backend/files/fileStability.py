import time
from backend.detection.config import stabilityThresholds
    
def stability(lastModifiedTime):
    curTime= time.monotonic()
    threshold= stabilityThresholds["event_threshold"]
    rem= curTime-lastModifiedTime+threshold
    if rem==0:
        return True
    else:
        return rem