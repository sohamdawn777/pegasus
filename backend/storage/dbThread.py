from backend.storage import dbStorage
import sqlite3
import threading
import queue
import time
from backend.utils.helpers import QueueHelper

dbOps = {
    "store_hashes": dbStorage.storeHashes,
    "fetch_hashes": dbStorage.fetchHashes,
    "update_file_paths": dbStorage.updateFilePaths,
    "update_file_stat_del1": dbStorage.updateFileStatDel1,
    "update_file_stat_del2": dbStorage.updateFileStatDel2,
    "fetch_safe_hashes": dbStorage.fetchSafeHahses,
    "remove_hashes": dbStorage.removeHashes
}

class DBThread(threading.Thread):
    def __init__(self, db_path):
        super().__init__()
        self.dbQueue= queue.Queue(maxsize= 100)
        self.dbEvent= threading.Event()
        self.db_path= db_path
    def run(self):
        conn= sqlite3.connect(self.db_path)
        cur= conn.cursor()
        dbStorage.tables(cur)
        while not self.dbEvent.is_set():
            try:
                taskObj= self.dbQueue.get(block= True, timeout= 1)
                task= taskObj["operation"]
                params= taskObj["params"]
                if taskObj["resp"]==None:
                    task(cur, conn, *params)
                else:
                    result= task(cur, *params)
                    response= QueueHelper.helper(taskObj["resp"], result, 3)
                    if response:
                        pass
                    else:
                        print("fetch failed.")
            except queue.Empty:
                time.sleep(0.5)
                continue
        conn.close()
        return

