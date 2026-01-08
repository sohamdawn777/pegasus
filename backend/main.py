import os
import time
from backend.backup.snapshots import Snapshots
from backend.detection.folderMonitior import EventHandler
from backend.detection.intentClassifier import IntentClassifier
from backend.detection.processMonitor import ProcessMonitor
from backend.backup.restoreBackup import RestoreBackup
from backend.backup.gcs import EncBackup
from backend.files.fileThread import FileThread
from backend.storage.dbThread import DBThread
from backend.detection.scheduler import Scheduler
from backend.files.fileAuditor import FileAuditor
from backend.files.versionController import VersionController
from backend.detection.sharedState import cond
from watchdog.observers import Observer

try:
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "crypto.txt"), "rb") as f:
        salt= f.read()
except FileNotFoundError:  
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "crypto.txt"), "wb") as f:
        salt= os.urandom(16)
        f.write(salt)

print("[BOOT] WELCOME TO PEGASUS....")
print("[BOOT] AGENT INITIALIZED...")
passKey= input("[BOOT] ENTER YOUR SPECIFIC PASSKEY FOR OFFSITE BACKUP OR CREATE A NEW ONE: ")

test_dir= os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_folder")
snapshot_dir= os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "snapshots")  
restore_dir= os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "restored_test_folder") 

os.makedirs(snapshot_dir, exist_ok= True)

dbInst= DBThread()
dbEvent= dbInst.dbEvent

fileInst= FileThread(dbInst.dbQueue)
fileInst1Event= fileInst.fileEvent

event_handler= EventHandler(test_dir, snapshot_dir, dbInst.dbQueue, fileInst.fileQueue)


schedulerInst= Scheduler(fileInst.fileQueue, test_dir, snapshot_dir, dbInst.dbQueue)
schedulerInstEvent= schedulerInst.schedulerEvent

fileAuditorInst= FileAuditor(snapshot_dir, fileInst.fileQueue, dbInst.dbQueue)
fileAuditorInstEvent= fileAuditorInst.fileAuditEvent

versionControllerInst= VersionController(snapshot_dir, dbInst.dbQueue)
versionControllerEvent= versionControllerInst.versionControlEvent

intentClassifierInst= IntentClassifier(test_dir)
intentClassifierEvent= intentClassifierInst.intentEvent

processMonitorInst= ProcessMonitor(test_dir, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
processMonitorEvent= processMonitorInst.processEvent

restoreBackupInst= RestoreBackup(dbInst.dbQueue, test_dir, snapshot_dir, restore_dir)
restoreBackupEvent= restoreBackupInst.backupEvent

encBackupInst= EncBackup(dbInst.dbQueue, test_dir, restore_dir, snapshot_dir, passKey, salt)
encBackupEvent= encBackupInst.gcsEvent

snapshots= Snapshots(snapshot_dir, fileInst.fileQueue)

dbInst.start()
fileInst.start()

observer= Observer()
observer.schedule(event_handler, test_dir, recursive= True)
observer.start()
intentClassifierInst.start()
processMonitorInst.start()

restoreBackupInst.start()
encBackupInst.start()
schedulerInst.start()
versionControllerInst.start()
fileAuditorInst.start()
snapshots.backup(test_dir)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("[BOOT] SHUTTING DOWN AGENT...")
finally:
    observer.stop()
    observer.join()

    schedulerInstEvent.set()
    with cond:
        cond.notify_all()
    schedulerInst.join()

    intentClassifierEvent.set()
    with cond:
        cond.notify_all()
    intentClassifierInst.join()

    processMonitorEvent.set()
    processMonitorInst.join()

    restoreBackupEvent.set()
    restoreBackupInst.join()

    encBackupEvent.set()
    encBackupInst.join()

    versionControllerEvent.set()
    versionControllerInst.join()

    fileAuditorInstEvent.set()
    fileAuditorInst.join()

    fileInst1Event.set()
    fileInst.join()

    dbEvent.set()
    dbInst.join()