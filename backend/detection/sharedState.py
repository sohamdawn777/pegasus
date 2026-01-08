import threading

fileDict= {}
heap= []
state= "SAFE"

lock= threading.Lock()
cond= threading.Condition(lock)

criticalState= threading.Event()
restoreState= threading.Event()
gcsState= threading.Event()