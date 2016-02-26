import jwt
import random
import string
from datetime import datetime, timedelta
import time


def generate_user_secret():
    """
    Generates a random secret string for use in user tokens.
    :return: secret string of length 'length'
    """
    length = 32
    secret = ''.join(random.choice(string.printable) for _ in range(length))
    return secret


def generate_user_token(username, is_admin, expiration, secret):
    """
    Generates a user token.
    :param username: the username of the recipient of the token
    :param is_admin: boolean set True if the token holder is an admin
    :param expiration: time in seconds before the token expires
    :param secret: secret string used to verify the token
    :return: user token
    """
    payload = {
        'exp': datetime.utcnow() + timedelta(seconds=expiration),
        'username': username,
        'is_admin': is_admin
    }
    token = jwt.encode(payload, secret, algorithm='HS512')
    return token


def validate_user_token(token, secret):
    """
    Validate a token against a secret.
    :param token: user token to be validated
    :param secret: secret against which to validate token
    :return: boolean, True if token is valid
    """
    try:
        payload = jwt.decode(token, secret, algorithms=['HS512'])
        return True
    except jwt.ExpiredSignature:
        # token expired
        return False
    except jwt.DecodeError:
        # token does not match secret
        return False
    except jwt.InvalidTokenError:
        # token invalid
        return False
    except Exception as e:
        # unhandled failure decoding
        return False


def test():
    """
    Test the functionality of the token module.
    :return: N/A
    """
    expiration_time = 5  # seconds
    username = "test"
    is_admin = True
    payload = {

    }

    print("Generating secret...")
    secret = generate_user_secret()
    print("Generated!\n")

    print("Generating token...")
    token = generate_user_token(username, is_admin, expiration_time, secret)
    print("Generated!\n")

    print("Testing validation...")
    assert validate_user_token(token, secret), "Proper validation failed"
    print("Success!\n")

    print("Testing improper validation...")
    assert not validate_user_token(token, 'wrong'), "Improper validation succeeded"
    print("Success!\n")

    print("Testing token expiration...")
    time.sleep(expiration_time + 1)
    assert not validate_user_token(token, secret), "Token expiration failed"
    print("Success!\n")

    print("Test complete.")


if __name__ == '__main__':
    test()
