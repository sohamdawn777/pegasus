import os
import time
from dotenv  import load_dotenv
from backend.backup.snapshots import Snapshots
from backend.detection.folderMonitior import EventHandler
from backend.detection.intentClassifier import IntentClassifier
from backend.detection.processMonitor import ProcessMonitor
from backend.backup.restoreBackup import RestoreBackup
from backend.files.fileThread import FileThread
from backend.storage.dbThread import DBThread
from backend.detection.scheduler import Scheduler
from backend.files.fileAuditor import FileAuditor
from backend.files.versionController import VersionController
from backend.detection.sharedState import cond
from watchdog.observers import Observer

load_dotenv()
os.makedirs(os.path.join(os.path.realpath(os.path.dirname(os.path.dirname(__file__))), ".pegasus"), exist_ok= True)
root_dir= os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".pegasus"))
try:
    with open(os.path.join(root_dir, "systemDB.db"), "rb") as f:
        pass
except FileNotFoundError:
    with open(os.path.join(root_dir, "systemDB.db"), "wb") as f:
        pass

print("[BOOT] WELCOME TO PEGASUS....")
print("[BOOT] AGENT INITIALIZED...")

test_dir= os.path.realpath(os.environ["MONITOR_PATH"])
snapshot_dir= os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".pegasus", "snapshots"))
restore_dir= os.path.realpath(os.environ["RESTORE_PATH"])
db_path= os.path.realpath(os.path.join(root_dir, "systemDB.db"))

os.makedirs(snapshot_dir, exist_ok= True)

dbInst= DBThread(db_path)
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

snapshots= Snapshots(snapshot_dir, fileInst.fileQueue)

dbInst.start()
fileInst.start()

observer= Observer()
observer.schedule(event_handler, test_dir, recursive= True)
observer.start()
intentClassifierInst.start()
processMonitorInst.start()

restoreBackupInst.start()
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

    versionControllerEvent.set()
    versionControllerInst.join()

    fileAuditorInstEvent.set()
    fileAuditorInst.join()

    fileInst1Event.set()
    fileInst.join()

    dbEvent.set()
    dbInst.join()