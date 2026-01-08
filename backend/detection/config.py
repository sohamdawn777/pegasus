stabilityThresholds= {
    "event_threshold": 1
}

auditThresholds= {
    "delete_scheduling": 120  #86400
}

fileSizeThresholds= {
    "small": 4096,
    "medium": 1048576,
    "large": 104857600,
}

classificationThresholds= {
    "on_modified_threshold": {"SAFE": 2, "CRITICAL": 5},
    "deltas": {"SAFE": 0.3, "CRITICAL": 0.1},
    "ratios": {"SAFE": 0.4, "CRITICAL": 0.5}
}

timeWindows= {
    "signalWindow": 2,
    "deEscWindow": 10
    }

deEscalationThreshold= 5

asciiRatios= {
    "text-like": 0.7,
    "binary": 0.3
}

entropyDeltaThresholds = {
    "low": 0.9,      # text, structured, databases
    "medium": 0.7,   # compressed / container formats
    "high": 0.3,     # already-high-entropy media
    "unknown": 0.6   # fallback when magic bytes fail
}

magicBytes = {
    "jpg": {
        "magic": b"\xFF\xD8\xFF",
        "entropyClass": "high"
    },
    "png": {
        "magic": b"\x89PNG\r\n\x1A\n",
        "entropyClass": "high"
    },
    "mp3": {
        "magic": b"\x49\x44\x33",
        "entropyClass": "high"
    },

    "mp4": {
        "magic": b"ftyp",
        "entropyClass": "medium"
    },
    "zip": {
        "magic": b"PK\x03\x04",
        "entropyClass": "medium"
    },
    "docx": {
        "magic": b"PK\x03\x04",
        "entropyClass": "medium"
    },
    "xlsx": {
        "magic": b"PK\x03\x04",
        "entropyClass": "medium"
    },
    "pptx": {
        "magic": b"PK\x03\x04",
        "entropyClass": "medium"
    },

    "pdf": {
        "magic": b"%PDF-",
        "entropyClass": "low"
    },
    "doc": {
        "magic": b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1",
        "entropyClass": "low"
    },
    "xls": {
        "magic": b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1",
        "entropyClass": "low"
    },
    "ppt": {
        "magic": b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1",
        "entropyClass": "low"
    },
    "db": {
        "magic": b"SQLite format 3\x00",
        "entropyClass": "low"
    }
}

restore_threshold= 15