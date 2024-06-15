from typing import Annotated, Union # type:ignore
from fastapi import Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserAuth(BaseModel):
    username: str
    email: str
    is_active: Union[bool, None] = None

# Auth
def test_decoder(token):
    return UserAuth(
        username = token + "test_decoder", email = "test@soujunior.com" 
    )

async def get_test_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = test_decoder(token)
    return user 