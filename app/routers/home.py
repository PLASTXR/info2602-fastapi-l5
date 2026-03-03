from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import AuthDep, IsUserLoggedIn
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status
from . import templates

home_router = APIRouter()

@home_router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    user_logged_in: IsUserLoggedIn
):
    if user_logged_in:
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@home_router.get("/app", response_class=HTMLResponse)
async def app_dashbaord(
    request: Request,
    user: AuthDep # The AuthDep dependency will check if the user is authenticated by verifying the access token in the cookie. If the user is authenticated, it will return the user object which can be used in the route function. If not authenticated, it will raise an HTTPException and prevent access to this route. This ensures that only authenticated users can access the dashboard of the app.
):
    return templates.TemplateResponse( # Render the todo.html template when the user navigates to /app. This is the main dashboard of the app where users can manage their todos. The template extends layout.html which contains the common layout for all pages.
        request=request, 
        name="todo.html",
        context={
            "current_user": user # Pass the user object to the template context so that we can access the current user's information in the template. For example, we can display the user's username on the dashboard.
        }
    )