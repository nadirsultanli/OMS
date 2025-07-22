from fastapi import Depends
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User

# Simple alias for getting current user - much cleaner in endpoints
current_user = Depends(get_current_user)

# You can now use this in your endpoints like:
# async def some_endpoint(user: User = current_user):
#     # user is automatically the authenticated user
#     pass 