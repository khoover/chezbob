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


def generate_user_token(username, is_admin, exp, secret):
    """
    Generates a user token.
    :param username: the username of the recipient of the token
    :param is_admin: boolean set True if the token holder is an admin
    :param exp: time in seconds before the token expires
    :param secret: secret string used to verify the token
    :return: user token
    """
    token = jwt.encode({'exp': datetime.utcnow() + timedelta(seconds=exp),
                        'username': username,
                        'is_admin': is_admin},
                       secret,
                       algorithm='HS512')
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


if __name__ == '__main__':
    s = generate_user_secret()
    t = generate_user_token('brown', True, 5, s)
    assert validate_user_token(t, s)
    assert not validate_user_token(t, 'wrong')
    time.sleep(6)
    assert not validate_user_token(t, s)
