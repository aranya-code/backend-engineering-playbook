"""
Tasks router module for dispatching background tasks.
"""
from fastapi import APIRouter
from services.task_service import queue_background_task
router=APIRouter()
@router.post('/tasks')
def tasks(): 
    # Dispatches a task to be processed asynchronously
    queue_background_task(); 
    return {'message':'Task queued successfully.'}
