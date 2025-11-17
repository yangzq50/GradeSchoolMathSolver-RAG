"""
Database Service Module

Provides centralized database access with abstract interface for easy backend switching.
"""
from .service import DatabaseService, get_database_service

__all__ = ['DatabaseService', 'get_database_service']
