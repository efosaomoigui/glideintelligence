from app.utils.security import get_password_hash, verify_password

try:
    pwd = "test"
    hashed = get_password_hash(pwd)
    print(f"Hash success: {hashed}")
    assert verify_password(pwd, hashed)
    print("Verify success")
except Exception as e:
    print(f"Hashing failed: {e}")
