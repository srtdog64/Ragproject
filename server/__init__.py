"""
Server package
"""
from .main import app
from .dependencies import (
    get_container,
    get_ingester,
    get_pipeline_builder
)

__all__ = [
    'app',
    'get_container',
    'get_ingester',
    'get_pipeline_builder'
]
