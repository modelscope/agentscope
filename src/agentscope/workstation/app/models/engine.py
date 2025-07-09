# -*- coding: utf-8 -*-
"""Module for engine related functions."""
from sqlmodel import create_engine
from app.core.config import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
