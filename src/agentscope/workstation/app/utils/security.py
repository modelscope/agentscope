# -*- coding: utf-8 -*-
"""password related securiy"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """get password"""
    return pwd_context.hash(password)


#
# if __name__ == '__main__':
#     print(get_password_hash("12345678"))
