EXTERNAL_SCRIPT = "external"
INLINE_SCRIPT = "inline"
SHORT_HASH_LENGTH = 12


def external_scripts(scan: dict) -> list[dict]:
    return [script for script in scan["scripts"] if script["kind"] == EXTERNAL_SCRIPT]


def inline_scripts(scan: dict) -> list[dict]:
    return [script for script in scan["scripts"] if script["kind"] == INLINE_SCRIPT]


def short_hash(sha256_hex: str) -> str:
    return sha256_hex[:SHORT_HASH_LENGTH]
