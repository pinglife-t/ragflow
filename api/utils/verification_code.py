import random
import string
import time
import json
from typing import Tuple, Optional

from rag.utils.redis_conn import REDIS_CONN

# Constants
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY = 600  # 10 minutes in seconds
VERIFICATION_CODE_PREFIX = "email_verification:"
VERIFICATION_CODE_LIMIT_PREFIX = "email_verification_limit:"
VERIFICATION_CODE_LIMIT = 5  # Maximum number of attempts in the time window
VERIFICATION_CODE_LIMIT_WINDOW = 3600  # 1 hour in seconds


def generate_verification_code(length: int = VERIFICATION_CODE_LENGTH) -> str:
    """
    Generate a random verification code of specified length.
    
    Args:
        length: Length of the verification code
        
    Returns:
        A random string of digits
    """
    return ''.join(random.choices(string.digits, k=length))


def store_verification_code(email: str, code: str, expiry: int = VERIFICATION_CODE_EXPIRY) -> bool:
    """Store the verification code with expiry time"""
    key = f"{VERIFICATION_CODE_PREFIX}{email}"
    try:
        # Store code and expiry time
        data = {
            'code': code,
            'expires_at': int(time.time()) + expiry
        }
        json_data = json.dumps(data)
        print(f"Storing verification code for {email}: {json_data}")
        REDIS_CONN.set(key, json_data)
        
        # Verify storage was successful
        stored = REDIS_CONN.get(key)
        if stored:
            if isinstance(stored, bytes):
                stored = stored.decode('utf-8')
            print(f"Verification code stored successfully: {stored}")
        else:
            print(f"Failed to store verification code for {email}")
        
        return True
    except Exception as e:
        print(f"Error storing verification code: {str(e)}")
        return False


def verify_code(email: str, code: str) -> bool:
    """Verify the provided code"""
    key = f"{VERIFICATION_CODE_PREFIX}{email}"
    try:
        stored_data = REDIS_CONN.get(key)
        print(f"Verifying code for {email}. Stored data: {stored_data}")
        
        if not stored_data:
            print(f"No verification code found for {email}")
            return False
            
        if isinstance(stored_data, bytes):
            stored_data = stored_data.decode('utf-8')
            
        print(f"Decoded stored data: {stored_data}")
        
        try:
            data = json.loads(stored_data)
        except json.JSONDecodeError as e:
            return False
            
        stored_code = data.get('code')
        expires_at = data.get('expires_at', 0)
        
        print(f"Stored code: {stored_code}, Provided code: {code}")
        print(f"Expires at: {expires_at}, Current time: {int(time.time())}")
        
        # Check if expired
        if time.time() > expires_at:
            print(f"Verification code expired for {email}")
            REDIS_CONN.REDIS.delete(key)
            return False
            
        # Verify code
        is_valid = stored_code == code
        print(f"Code validation result: {is_valid}")
        
        # If validation successful, delete the code
        if is_valid:
            print(f"Deleting verification code for {email}")
            REDIS_CONN.REDIS.delete(key)            
        return is_valid
    except Exception as e:
        print(f"Error verifying code: {str(e)}")
        return False


def can_send_verification_code(email: str) -> Tuple[bool, int]:
    """Check if the email can receive a new verification code"""
    limit_key = f"{VERIFICATION_CODE_LIMIT_PREFIX}{email}"
    try:
        stored_data = REDIS_CONN.get(limit_key)
        current_time = int(time.time())
        
        # If no data, initialize counter
        if not stored_data:
            data = {
                'count': 1,
                'expires_at': current_time + VERIFICATION_CODE_LIMIT_WINDOW
            }
            REDIS_CONN.set(limit_key, json.dumps(data))
            return True, 0
            
        # If data is integer (old format), convert to new format
        if isinstance(stored_data, int) or (isinstance(stored_data, bytes) and stored_data.isdigit()):
            count = int(stored_data if isinstance(stored_data, int) else stored_data.decode('utf-8'))
            data = {
                'count': count,
                'expires_at': current_time + VERIFICATION_CODE_LIMIT_WINDOW
            }
            REDIS_CONN.set(limit_key, json.dumps(data))
        else:
            # Normal JSON data
            if isinstance(stored_data, bytes):
                stored_data = stored_data.decode('utf-8')
            data = json.loads(stored_data)
            
        count = data.get('count', 0)
        expires_at = data.get('expires_at', 0)
        
        # Check if expired
        if current_time > expires_at:
            # Reset counter
            data = {
                'count': 1,
                'expires_at': current_time + VERIFICATION_CODE_LIMIT_WINDOW
            }
            REDIS_CONN.set(limit_key, json.dumps(data))
            return True, 0
            
        # Check if over limit
        if count >= VERIFICATION_CODE_LIMIT:
            remaining_time = expires_at - current_time
            return False, max(0, remaining_time)
            
        # Increment counter
        data['count'] = count + 1
        REDIS_CONN.set(limit_key, json.dumps(data))
        return True, 0
        
    except Exception as e:
        print(f"Error checking rate limit: {str(e)}")
        return True, 0  # Allow sending when error occurs
