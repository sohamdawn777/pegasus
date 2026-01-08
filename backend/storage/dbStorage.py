def tables(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS hashes (id INTEGER PRIMARY KEY AUTOINCREMENT, file_uuid TEXT NOT NULL, file_path TEXT NOT NULL, hash_value TEXT NOT NULL, is_deleted INTEGER NOT NULL, deleted_at REAL, safe_to_delete_at REAL, physically_deleted_at REAL, is_attacked INTEGER NOT NULL, timestamp REAL NOT NULL)''')
def storeHashes(cur, conn, file_uuid, file_path, hash_value, is_deleted, deleted_at, safe_to_delete_at, physically_deleted_at, is_attacked, timestamp):
    cur.execute('''INSERT INTO hashes (file_uuid, file_path, hash_value, is_deleted, deleted_at, safe_to_delete_at, physically_deleted_at, is_attacked, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (file_uuid, file_path, hash_value, is_deleted, deleted_at, safe_to_delete_at, physically_deleted_at, is_attacked, timestamp))
    conn.commit()
def fetchHashes(cur, is_del, curTime):
    cur.execute('''SELECT * FROM hashes WHERE is_deleted= ? AND safe_to_delete_at <= ? AND physically_deleted_at IS NULL ORDER BY safe_to_delete_at LIMIT 25''', (is_del, curTime))
    rows= cur.fetchall()
    return rows
def updateFilePaths(cur, conn, old_file_path, new_file_path):
    cur.execute('''UPDATE hashes SET file_path= ? WHERE file_path= ?''', (new_file_path, old_file_path)) 
    conn.commit()  
def updateFileStatDel1(cur, conn, file_path, is_deleted, deleted_at, safe_to_delete_at, physically_deleted_at):
    cur.execute('''UPDATE hashes SET is_deleted= ?, deleted_at= ?, safe_to_delete_at= ?, physically_deleted_at= ? WHERE file_path= ?''', (is_deleted, deleted_at, safe_to_delete_at, physically_deleted_at, file_path))
    conn.commit()
def updateFileStatDel2(cur,  conn, is_deleted, delAt, safeAt, finalAt):
    cur.execute('''UPDATE hashes SET is_deleted= ?, deleted_at= ?, safe_to_delete_at= ?, physically_deleted_at= ? WHERE id NOT IN (SELECT MAX(id) FROM hashes GROUP BY file_path) AND is_deleted= 0''', (is_deleted, delAt, safeAt, finalAt))
    conn.commit()
def fetchSafeHahses(cur, is_attacked, is_deleted, threshold):
    cur.execute('''SELECT * FROM hashes WHERE is_attacked= ? AND is_deleted= ? AND timestamp<= ?''', (is_attacked, is_deleted, threshold))
    rows= cur.fetchall()
    return rows
def removeHashes(cur, conn, physically_deleted_at, file_uuid):
    cur.execute('''UPDATE hashes SET physically_deleted_at= ? WHERE file_uuid= ?''', (physically_deleted_at, file_uuid))
    conn.commit()