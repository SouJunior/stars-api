from typing import Annotated, Union # type:ignore
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserAuth(BaseModel):
    username: str
    email: str
    is_active: Union[bool, None] = None

class UserInDB(UserAuth):
    hashed_password: str

# Auth
def test_decoder(token):
    return UserAuth(
        username = token + "test_decoder", email = "test@soujunior.com" 
    )

async def get_test_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = test_decoder(token)
    return user 

def fake_hashed_password(password: str):
    return "fakehashed" + password

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decoder_token(token):
    user = get_user(get_db, token)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decoder_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user

async def get_current_activate_user(current_user: Annotated[UserAuth, Depend(get_current_user)],):
    if current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user