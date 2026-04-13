from fastapi import APIRouter, HTTPException, Depends, Request, Response, Form
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.utilities import flash
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status
from . import templates
from fastapi.responses import HTMLResponse, RedirectResponse

auth_router = APIRouter(tags=["Authentication"])

@auth_router.post("/login")
async def login_action(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep,
    request: Request
) -> Response:
    user = db.exec(select(User).where(User.username == form_data.username)).one_or_none()
    if not user or not verify_password(plaintext_password=form_data.password, encrypted_password=user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role},)

    max_age = 1 * 24 * 60 * 60 # (1 day converted to secs) Set the cookie to expire in 1 day
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER) # redirect to the homepage after successful login
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=max_age, samesite="lax") # Set the access token in a cookie. httponly means it cannot be accessed by client-side scripts(proteching it aginst cross site scripting attacks), max_age sets the expiration time of the cookie. 
    
    # Samesite lax means the cookie is not sent on cross-site requests, but is sent when the user navigates to the site from an external link this samesite protects against CSRF attacks.
    
    flash(request, "Logged in successfully") # Flash a success message to be displayed on the homepage after redirection. Check the flash function in utilities.py for more details on how it works.

    return response


# The form of the signup page in signup.html will direct the user to the signup action route because the path(signup) and method(post) of the route maps onto the action and method attributes of the form in signup.html
@auth_router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup_user(request:Request, db:SessionDep, username: Annotated[str, Form()], email: Annotated[str, Form()], password: Annotated[str, Form()],):
    try:
        new_user = RegularUserCreate(
            username=username, 
            email=email, 
            password=encrypt_password(password)
        )
        new_user_db = User.model_validate(new_user)
        db.add(new_user_db)
        db.commit()
        flash(request, "Registration completed! Sign in now!")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER) # redirect to the login page after successful registration
    except Exception as e:
        print(e)
        db.rollback()
        raise HTTPException(
                    status_code=400,
                    detail="Username or email already exists",
                    headers={"WWW-Authenticate": "Bearer"},
                )

# exercise 
@auth_router.get("/logout")
def logout_user(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    flash(request, "Logged out successfully")
    return response

@auth_router.get("/identify", response_model=UserResponse)
def get_user_by_id(db: SessionDep, user:AuthDep):
    return user


@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="login.html", # direct to the login.html template which extends layout.html
    )

@auth_router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="signup.html", # direct to the signup.html template which extends layout.html
    )