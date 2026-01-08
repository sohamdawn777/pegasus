import os
import stat
import time
import queue
import math
from collections import Counter
from backend.detection.config import fileSizeThresholds

class QueueHelper:
    @staticmethod
    def helper(queueObj, taskObj, retryLimit):
        enqueueSuccess= False        
        try:
            queueObj.put(taskObj, block= True, timeout= 1)
            enqueueSuccess= True
        except queue.Full:
            while (not enqueueSuccess) and (retryLimit>0):
                try:
                    queueObj.put(taskObj, block= True, timeout= 1)
                except queue.Full:
                    retryLimit-=1
                    time.sleep(1)
                    continue
        return enqueueSuccess

class Sampler:
    @staticmethod
    def helper(fileObj):
            fileSize= os.fstat(fileObj.fileno()).st_size
            offset= min(fileSizeThresholds["small"], fileSize)
            if fileSize<=fileSizeThresholds["small"]:
                data= fileObj.read()
            elif fileSize>fileSizeThresholds["small"] and fileSize<=fileSizeThresholds["medium"]:
                n= offset
                s1= fileObj.read(n)
                fileObj.seek(-min(n, fileSize), 2)
                s2= fileObj.read(n)
                data= s1+s2
            elif fileSize>fileSizeThresholds["medium"] and fileSize<=fileSizeThresholds["large"]:
                n= offset*2
                s1= fileObj.read(n)
                fileObj.seek(-min(n, fileSize), 2)
                s2= fileObj.read(n)
                data= s1+s2
            else:
                n= offset*4
                s1= fileObj.read(n)
                fileObj.seek(-min(n, fileSize), 2)
                s2= fileObj.read(n)
                data= s1+s2
            return data

class EntropyCalc:
    @staticmethod
    def helper(data):
        frequency= Counter(data)
        total= 0
        if len(data)!=0:
            for k in frequency:
                total+=(frequency[k]/len(data))*math.log((frequency[k]/len(data)), 2)
            entropy= -total
        else:
            entropy= 0
        return entropy

class AsciiRatio:
    @staticmethod
    def helper(data):
        frequency= Counter(data)
        count= 0
        if len(data)!=0:
            for i in frequency:
                if (i>=32 and i<=126) or (i in (9, 10, 13)):
                    count+=frequency[i]
            asciiRatio= count/len(data)
        else:
            asciiRatio= 0
        return asciiRatio
    
class Containment:
    @staticmethod
    def helper(directory):
        fileLst= []
        dirLst= []
        root= None
        fileIterator= os.walk(directory)
        for i in fileIterator:
            if root==None:
                root= i[0]

            for j in i[1]:
                dirLst.append(os.path.join(i[0], j))
                
            for k in i[2]:
                fileLst.append(os.path.join(i[0], k))
        dirLst.sort(reverse= True)
        try:
            for i in fileLst:
                os.chmod(i, stat.S_IRUSR |
                     stat.S_IRGRP |
                     stat.S_IROTH)
            for i in dirLst:
                os.chmod(i, stat.S_IRUSR | stat.S_IXUSR |
                         stat.S_IRGRP | stat.S_IXGRP |
                         stat.S_IROTH | stat.S_IXOTH)
            os.chmod(root, stat.S_IRUSR | stat.S_IXUSR |
                         stat.S_IRGRP | stat.S_IXGRP |
                         stat.S_IROTH | stat.S_IXOTH)
        except PermissionError:
            print("Permission Denied...")