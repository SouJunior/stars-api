from __future__ import print_function

import os
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

import sib_api_v3_sdk # type:ignore
from sib_api_v3_sdk.rest import ApiException  # type:ignore
from pprint import pprint
from fastapi.middleware.cors import CORSMiddleware

from app import crud, models, schemas
from app.database import SessionLocal, engine

from app.settings import settings
from app.auth import oauth2_scheme, authenticate_user, create_access_token, get_current_user, get_current_active_user
from typing import Annotated, Optional
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI
from datetime import datetime, timedelta
from app.database import get_db
from app import utils

models.Base.metadata.create_all(bind=engine)


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:8080",
    "https://stars.soujunior.tech",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/token", response_model=schemas.Token, summary="Login para obter token de acesso", description="Autentica um usuário com email e senha e retorna um token JWT para acesso a rotas protegidas.")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not settings.JWT_EXPIRE_MINUTES:
        raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES cannot be None")

    access_token_expires = timedelta(minutes=float(settings.JWT_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User, summary="Obter usuário autenticado", description="Retorna os detalhes do usuário atualmente autenticado.")
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = utils.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User], summary="Listar usuários", description="Retorna uma lista de todos os usuários. Requer autenticação.")
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    users = utils.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User, summary="Obter usuário por ID", description="Retorna os detalhes de um usuário específico pelo seu ID. Requer autenticação.")
def read_user(user_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    db_user = utils.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item, summary="Criar item para usuário", description="Cria um novo item associado a um usuário específico. Requer autenticação.")
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


# @app.get("/email")
# def read_items():
#     print("Email: ", )
#     try:
#         print("Email: ", os.getenv('BREVO_API_KEY'))
#         return
#         # api_response = api_instance.get_account()
#         # pprint(api_response)
#         api_response = api_instance.send_transac_email(send_smtp_email)
#         pprint(api_response)


#     except ApiException as e:
#         print("Exception when calling AccountApi->get_account: %s\n" % e)

#     return


# volunteer
@app.get("/volunteers/", response_model=list[schemas.VolunteerList])
def get_volunteers(skip: int = 0, limit: int = 100, name: Optional[str] = None, jobtitle_id: Optional[int] = None, db: Session = Depends(get_db)):
    db_volunteers = crud.get_volunteers(db, skip=skip, limit=limit, name=name, jobtitle_id=jobtitle_id)
    if db_volunteers is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return db_volunteers


# volunteer by email
@app.get("/volunteer/{email}", response_model=schemas.Volunteer)
def get_volunteers_by_email(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db), email: str = ""
):
    db_volunteer = crud.get_volunteer_by_email(db, email=email)
    if db_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return db_volunteer


@app.post("/volunteer", response_model=schemas.Volunteer)
def create_volunteer(volunteer: schemas.VolunteerCreate, db: Session = Depends(get_db)):
    db_user = crud.get_volunteer_by_email(db, email=volunteer.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")


    if volunteer.jobtitle_id <= 0:
        raise HTTPException(status_code=400, detail="We need jobtitle_id")

    vol = crud.create_volunteer(
        db=db, volunteer=volunteer, jobtitle_id=volunteer.jobtitle_id
    )
    # send_email(volunteer.email, volunteer.name)
    return vol


@app.get("/volunteers/{volunteer_id}", response_model=schemas.Volunteer)
def get_volunteer_by_id(
    volunteer_id: int, db: Session = Depends(get_db)
):
    db_volunteer = crud.get_volunteer_by_id(db, volunteer_id=volunteer_id)
    if db_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return db_volunteer


@app.patch("/volunteers/{volunteer_id}/status/", response_model=schemas.Volunteer)
def update_volunteer_status(
    volunteer_id: int,
    new_status_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user) # Assuming status updates are restricted to authenticated users
):
    # Check if the new_status_id is valid
    db_status = db.query(models.VolunteerStatus).filter(models.VolunteerStatus.id == new_status_id).first()
    if not db_status:
        raise HTTPException(status_code=404, detail="New status not found")

    updated_volunteer = crud.update_volunteer_status(db, volunteer_id, new_status_id)
    if updated_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return updated_volunteer


@app.get("/jobtitles/", response_model=list[schemas.JobTitle])
def get_jobtitles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_jobtitles = crud.get_jobtitles(db)
    if db_jobtitles is None:
        raise HTTPException(status_code=404, detail="JobTitles not found")
    return db_jobtitles


@app.post("/volunteer-statuses/", response_model=schemas.VolunteerStatus)
def create_volunteer_status(
    status: schemas.VolunteerStatusCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user) # Assuming status creation is restricted
):
    db_status = db.query(models.VolunteerStatus).filter(models.VolunteerStatus.name == status.name).first()
    if db_status:
        raise HTTPException(status_code=400, detail="Volunteer Status with this name already exists")
    return crud.create_volunteer_status(db=db, status=status)


@app.get("/volunteer-statuses/", response_model=list[schemas.VolunteerStatus])
def get_volunteer_statuses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_volunteer_statuses(db, skip=skip, limit=limit)


def send_email(email, name):
    print(
        "Email: ",
    )
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = os.getenv("BREVO_API_KEY")

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email, "name": name}],
            template_id=9,
            params={"name": name, "email": email},
            headers={
                "X-Mailin-custom": "custom_header_1:custom_value_1|custom_header_2:custom_value_2|custom_header_3:custom_value_3",
                "charset": "iso-8859-1",
            },
        )  # SendSmtpEmail | Values to send a transactional email

        print("Email: ", os.getenv("BREVO_API_KEY"))
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)

    except ApiException as e:
        print("Exception when calling AccountApi->get_account: %s\n" % e)

    return
