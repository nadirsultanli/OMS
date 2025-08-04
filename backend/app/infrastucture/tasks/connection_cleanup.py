"""
Celery task for cleaning up idle database connections
"""
from celery import shared_task
from app.infrastucture.database.connection import cleanup_idle_connections
from app.infrastucture.logs.logger import default_logger


@shared_task(bind=True, name='cleanup_idle_connections')
def cleanup_idle_connections_task(self):
    """
    Celery task to clean up idle database connections.
    This task should be scheduled to run every 2-5 minutes.
    """
    try:
        # Import asyncio to run the async function
        import asyncio
        
        # Run the cleanup function
        result = asyncio.run(cleanup_idle_connections())
        
        default_logger.info(f"Connection cleanup task completed successfully")
        return {
            'status': 'success',
            'message': 'Connection cleanup completed'
        }
        
    except Exception as e:
        default_logger.error(f"Connection cleanup task failed: {str(e)}")
        # Retry the task after 1 minute if it fails
        raise self.retry(countdown=60, max_retries=3)


# Example of how to schedule this task:
# To schedule this task to run every 2 minutes, add this to your Celery beat schedule:
#
# CELERY_BEAT_SCHEDULE = {
#     'cleanup-idle-connections': {
#         'task': 'cleanup_idle_connections',
#         'schedule': 120.0,  # 2 minutes
#     },
# } 