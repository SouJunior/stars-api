from __future__ import print_function

import os
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
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
@app.get("/volunteers/", response_model=list[schemas.Volunteer])
def get_volunteers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_volunteers = crud.get_volunteers(db)
    if db_volunteers is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return db_volunteers

# volunteer by email
@app.get("/volunteer/{email}", response_model=schemas.Volunteer)
def get_volunteers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), email: str = ''):
    db_volunteer = crud.get_volunteer_by_email(db, email=email)
    if db_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return db_volunteer

@app.post("/volunteer", response_model=schemas.Volunteer)
def create_volunteer(volunteer: schemas.VolunteerCreate, db: Session = Depends(get_db)):
    db_user = crud.get_volunteer_by_email(db, email=volunteer.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    vol =  crud.create_volunteer(db=db, volunteer=volunteer, jobtitle_id=volunteer.jobtitle_id[0].id)
    # send_email(volunteer.email, volunteer.name)
    return vol

@app.get("/jobtitles/", response_model=list[schemas.JobTitle])
def get_jobtitles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_jobtitles = crud.get_jobtitles(db)
    if db_jobtitles is None:
        raise HTTPException(status_code=404, detail="JobTitles not found")
    return db_jobtitles

def send_email(email, name):
    print("Email: ", )
    try: 

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=[{"email": email,"name": name}], template_id=1, params={"name": "John", "surname": "Doe"}, headers={"X-Mailin-custom": "custom_header_1:custom_value_1|custom_header_2:custom_value_2|custom_header_3:custom_value_3", "charset": "iso-8859-1"}) # SendSmtpEmail | Values to send a transactional email

        print("Email: ", os.getenv('BREVO_API_KEY'))
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)

    except ApiException as e:
        print("Exception when calling AccountApi->get_account: %s\n" % e)

    return 
