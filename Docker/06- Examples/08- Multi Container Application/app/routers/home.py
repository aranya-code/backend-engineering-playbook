"""
Home router module for basic endpoints.
"""
from fastapi import APIRouter
router=APIRouter()
@router.get('/')
def home(): 
    # Returns a simple status message
    return {'service':'Multi-Container Demo','status':'running'}
