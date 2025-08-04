from fastapi import Request

from .auth import UserManager


def get_user_manager(request: Request) -> UserManager:
    return request.app.state.user_manager
