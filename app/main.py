from __future__ import print_function

import os
from fastapi import Depends, FastAPI, HTTPException, status, Query
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
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app import utils, integrations

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
    if user.registration_code != settings.REGISTRATION_CODE:
        raise HTTPException(status_code=400, detail="Invalid registration code")
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


# volunteer
@app.get("/volunteers/", response_model=list[schemas.VolunteerList], summary="Listar voluntários", description="Retorna uma lista de voluntários com opções de filtro por nome, email, cargo, status e squad.")
def get_volunteers(
    skip: int = 0, 
    limit: int = 100, 
    name: Optional[str] = None, 
    email: Optional[str] = Query(None, description="Filtrar por email (busca parcial)"), 
    jobtitle_id: Optional[int] = None, 
    status_id: Optional[int] = None, 
    volunteer_type_id: Optional[int] = None,
    squad_id: Optional[int] = None,
    order: str = Query("desc", enum=["asc", "desc"], description="Ordenação por data de criação"),
    db: Session = Depends(get_db)
):
    db_volunteers = crud.get_volunteers(db, skip=skip, limit=limit, name=name, email=email, jobtitle_id=jobtitle_id, status_id=status_id, volunteer_type_id=volunteer_type_id, squad_id=squad_id, order=order)
    if db_volunteers is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return db_volunteers


# volunteer public search
@app.get("/volunteer/search", response_model=list[schemas.VolunteerPublic])
def search_volunteers_public(
    skip: int = 0, 
    limit: int = 100, 
    email: Optional[str] = Query(None, description="Filtrar por email (busca parcial)"),
    jobtitle_id: Optional[int] = Query(None, description="Filtrar por cargo"),
    db: Session = Depends(get_db)
):
    db_volunteers = crud.get_volunteers(
        db, skip=skip, limit=limit, 
        email=email, 
        jobtitle_id=jobtitle_id
    )
    return db_volunteers


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
    send_email(volunteer.email, volunteer.name)
    return vol


@app.get("/volunteers/{volunteer_id}", response_model=schemas.Volunteer)
def get_volunteer_by_id(
    volunteer_id: int, db: Session = Depends(get_db)
):
    db_volunteer = crud.get_volunteer_by_id(db, volunteer_id=volunteer_id)
    if db_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return db_volunteer


@app.get("/volunteers/{volunteer_id}/public", response_model=schemas.VolunteerPublic, summary="Obter perfil público do voluntário", description="Retorna os dados públicos do voluntário (sem telefone/email).")
def get_volunteer_public_profile(
    volunteer_id: int, db: Session = Depends(get_db)
):
    db_volunteer = crud.get_volunteer_by_id(db, volunteer_id=volunteer_id)
    if db_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return db_volunteer


@app.post("/volunteers/request-edit-link", summary="Solicitar link de edição", description="Envia um link com token para o email do voluntário para edição de perfil.")
def request_edit_link(
    request: schemas.VolunteerUpdateLinkRequest,
    db: Session = Depends(get_db)
):
    volunteer = crud.create_volunteer_edit_token(db, request.email)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Email não encontrado")
    
    # Generate link (Hypothetical frontend URL)
    link = f"{settings.BASE_FRONTEND_URL}/volunteer/edit/{volunteer.edit_token}"
    
    utils.send_edit_link_email(volunteer.email, volunteer.name, link)
    return {"message": "Link de edição enviado para o e-mail."}


@app.get("/volunteers/edit/{token}", response_model=schemas.VolunteerWithEmail, summary="Obter dados para edição via token", description="Retorna os dados do voluntário se o token for válido e não expirado.")
def get_volunteer_for_edit(token: str, db: Session = Depends(get_db)):
    volunteer = crud.get_volunteer_by_token(db, token)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Link inválido")
    
    # Check expiry (UX check)
    now = datetime.now(timezone.utc)
    expiry = volunteer.edit_token_expires_at
    if expiry:
         if expiry.tzinfo is None:
             expiry = expiry.replace(tzinfo=timezone.utc)
         
         if expiry < now:
             raise HTTPException(status_code=400, detail="Link expirado")
    else:
         raise HTTPException(status_code=400, detail="Link inválido")

    return volunteer


@app.patch("/volunteers/edit/{token}", response_model=schemas.Volunteer, summary="Atualizar perfil via token", description="Atualiza os campos permitidos do voluntário. Respeita limite de 2 edições/dia.")
def update_volunteer_profile(
    token: str, 
    profile_data: schemas.VolunteerUpdateProfile, 
    db: Session = Depends(get_db)
):
    volunteer, error = crud.update_volunteer_profile_by_token(db, token, profile_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return volunteer


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


@app.patch("/volunteers/{volunteer_id}/squad/", response_model=schemas.Volunteer)
def update_volunteer_squad(
    volunteer_id: int,
    new_squad_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_squad = db.query(models.Squad).filter(models.Squad.id == new_squad_id).first()
    if not db_squad:
        raise HTTPException(status_code=404, detail="New squad not found")

    updated_volunteer = crud.update_volunteer_squad(db, volunteer_id, new_squad_id)
    if updated_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return updated_volunteer


@app.patch("/volunteers/{volunteer_id}/type/", response_model=schemas.Volunteer)
def update_volunteer_type(
    volunteer_id: int,
    new_type_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_type = db.query(models.VolunteerType).filter(models.VolunteerType.id == new_type_id).first()
    if not db_type:
        raise HTTPException(status_code=404, detail="New volunteer type not found")

    updated_volunteer = crud.update_volunteer_type(db, volunteer_id, new_type_id)
    if updated_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return updated_volunteer


@app.post("/volunteers/{volunteer_id}/check-apoiase", response_model=schemas.Volunteer, summary="Verificar status do APOIA.se", description="Verifica se o voluntário é um apoiador ativo no APOIA.se e atualiza o status.")
async def check_volunteer_apoiase(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    volunteer = crud.get_volunteer_by_id(db, volunteer_id=volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    
    is_supporter = await integrations.check_apoiase_status(volunteer.email)
    
    volunteer.is_apoiase_supporter = is_supporter
    db.commit()
    db.refresh(volunteer)
    
    return volunteer


@app.get("/volunteer-types/", response_model=list[schemas.VolunteerType])
def get_volunteer_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_volunteer_types(db, skip=skip, limit=limit)


# Verticals
@app.post("/verticals/", response_model=schemas.Vertical, summary="Criar Vertical", description="Cria uma nova vertical. Requer autenticação.")
def create_vertical(
    vertical: schemas.VerticalCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_vertical = db.query(models.Vertical).filter(models.Vertical.name == vertical.name).first()
    if db_vertical:
        raise HTTPException(status_code=400, detail="Vertical with this name already exists")
    return crud.create_vertical(db=db, vertical=vertical)

@app.get("/verticals/", response_model=list[schemas.VerticalWithVolunteers], summary="Listar Verticais", description="Retorna uma lista de todas as verticais com os voluntários associados.")
def get_verticals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_verticals(db, skip=skip, limit=limit)

@app.get("/verticals/{vertical_id}", response_model=schemas.VerticalWithVolunteers, summary="Obter Vertical por ID", description="Retorna os detalhes de uma vertical específica com os voluntários associados.")
def get_vertical(vertical_id: int, db: Session = Depends(get_db)):
    db_vertical = crud.get_vertical(db, vertical_id=vertical_id)
    if db_vertical is None:
        raise HTTPException(status_code=404, detail="Vertical not found")
    return db_vertical

@app.put("/verticals/{vertical_id}", response_model=schemas.Vertical, summary="Atualizar Vertical", description="Atualiza uma vertical existente. Requer autenticação.")
def update_vertical(
    vertical_id: int,
    vertical: schemas.VerticalUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    updated_vertical = crud.update_vertical(db, vertical_id=vertical_id, vertical=vertical)
    if updated_vertical is None:
        raise HTTPException(status_code=404, detail="Vertical not found")
    return updated_vertical

@app.delete("/verticals/{vertical_id}", response_model=schemas.Vertical, summary="Deletar Vertical", description="Deleta uma vertical existente. Requer autenticação.")
def delete_vertical(
    vertical_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_vertical = crud.delete_vertical(db, vertical_id=vertical_id)
    if db_vertical is None:
        raise HTTPException(status_code=404, detail="Vertical not found")
    return db_vertical

@app.patch("/volunteers/{volunteer_id}/verticals/", response_model=schemas.Volunteer, summary="Atualizar verticais do voluntário", description="Atualiza as verticais associadas a um voluntário. Requer autenticação.")
def update_volunteer_verticals(
    volunteer_id: int,
    vertical_ids: list[int],
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    updated_volunteer = crud.update_volunteer_verticals(db, volunteer_id, vertical_ids)
    if updated_volunteer is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return updated_volunteer


@app.post("/volunteer-types/", response_model=schemas.VolunteerType)
def create_volunteer_type(
    type_data: schemas.VolunteerTypeBase,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_type = db.query(models.VolunteerType).filter(models.VolunteerType.name == type_data.name).first()
    if db_type:
        raise HTTPException(status_code=400, detail="Volunteer Type with this name already exists")
    return crud.create_volunteer_type(db=db, type_data=type_data)


@app.get("/jobtitles/", response_model=list[schemas.JobTitle])
def get_jobtitles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_jobtitles = crud.get_jobtitles(db)
    if db_jobtitles is None:
        raise HTTPException(status_code=404, detail="JobTitles not found")
    return db_jobtitles


@app.post("/squads/", response_model=schemas.Squad)
def create_squad(
    squad: schemas.SquadCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_squad = db.query(models.Squad).filter(models.Squad.name == squad.name).first()
    if db_squad:
        raise HTTPException(status_code=400, detail="Squad with this name already exists")
    return crud.create_squad(db=db, squad=squad)


@app.get("/squads/", response_model=list[schemas.Squad])
def get_squads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_squads(db, skip=skip, limit=limit)


@app.get("/squads/{squad_id}", response_model=schemas.Squad)
def get_squad(squad_id: int, db: Session = Depends(get_db)):
    db_squad = crud.get_squad(db, squad_id=squad_id)
    if db_squad is None:
        raise HTTPException(status_code=404, detail="Squad not found")
    return db_squad


@app.put("/squad/{squad_id}", response_model=schemas.Squad)
def update_squad(
    squad_id: int,
    squad: schemas.SquadUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    updated_squad = crud.update_squad(db, squad_id=squad_id, squad=squad)
    if updated_squad is None:
        raise HTTPException(status_code=404, detail="Squad not found")
    return updated_squad


@app.delete("/squad/{squad_id}", response_model=schemas.Squad)
def delete_squad(
    squad_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_squad = crud.delete_squad(db, squad_id=squad_id)
    if db_squad is None:
        raise HTTPException(status_code=404, detail="Squad not found")
    return db_squad


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


@app.get("/dashboard/stats", response_model=schemas.DashboardStats, summary="Estatísticas do Dashboard", description="Retorna estatísticas para o dashboard, incluindo contagem de voluntários por status e cadastros realizados hoje.")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_active_user)):
    return crud.get_dashboard_stats(db)


def send_email(email, name):
    if not os.getenv("BREVO_API_KEY"):
        print("BREVO_API_KEY not set, skipping email.")
        return

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
            params={"name": name, "email": email, "contact": {"NAME": name}, "NOME": name},
            headers={
                "X-Mailin-custom": "custom_header_1:custom_value_1|custom_header_2:custom_value_2|custom_header_3:custom_value_3",
                "charset": "iso-8859-1",
            },
        )  # SendSmtpEmail | Values to send a transactional email

        print("Email: ", os.getenv("BREVO_API_KEY") )
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)

    except ApiException as e:
        print("Exception when calling AccountApi->get_account: %s\n" % e)

    return


# Projects
@app.post("/projects/", response_model=schemas.Project, summary="Criar projeto", description="Cria um novo projeto. Requer autenticação.")
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    return crud.create_project(db=db, project=project)

@app.get("/projects/", response_model=list[schemas.Project], summary="Listar projetos", description="Retorna uma lista de todos os projetos. Requer autenticação.")
def get_projects(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    return crud.get_projects(db, skip=skip, limit=limit)

@app.get("/projects/{project_id}", response_model=schemas.Project, summary="Obter projeto por ID", description="Retorna os detalhes de um projeto específico. Requer autenticação.")
def get_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@app.delete("/projects/{project_id}", response_model=schemas.Project, summary="Deletar projeto", description="Deleta um projeto existente. Requer autenticação.")
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_project = crud.delete_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


# Feedback
@app.post("/volunteers/{volunteer_id}/feedbacks", response_model=schemas.FeedbackRead, summary="Criar feedback", description="Cria um novo feedback para um voluntário. Requer autenticação.")
def create_feedback(
    volunteer_id: int, 
    feedback: schemas.FeedbackCreate, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    # Check if volunteer exists
    db_volunteer = crud.get_volunteer_by_id(db, volunteer_id=volunteer_id)
    if not db_volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
        
    return crud.create_feedback(db=db, feedback=feedback, user_id=current_user.id, volunteer_id=volunteer_id)

@app.get("/volunteers/{volunteer_id}/feedbacks", response_model=list[schemas.FeedbackRead], summary="Listar feedbacks", description="Retorna os feedbacks de um voluntário.")
def get_feedbacks(
    volunteer_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    db_volunteer = crud.get_volunteer_by_id(db, volunteer_id=volunteer_id)
    if not db_volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return crud.get_feedbacks_for_volunteer(db, volunteer_id=volunteer_id, skip=skip, limit=limit)

@app.put("/feedbacks/{feedback_id}", response_model=schemas.FeedbackRead, summary="Atualizar feedback", description="Atualiza um feedback existente. Apenas o autor pode atualizar.")
def update_feedback(
    feedback_id: int, 
    feedback: schemas.FeedbackUpdate, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_feedback = crud.get_feedback(db, feedback_id=feedback_id)
    if not db_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
        
    if db_feedback.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this feedback")
        
    return crud.update_feedback(db, feedback_id=feedback_id, feedback=feedback)

@app.delete("/feedbacks/{feedback_id}", response_model=schemas.FeedbackRead, summary="Deletar feedback", description="Deleta um feedback existente. Apenas o autor pode deletar.")
def delete_feedback(
    feedback_id: int, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_feedback = crud.get_feedback(db, feedback_id=feedback_id)
    if not db_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
        
    if db_feedback.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this feedback")
        
    return crud.delete_feedback(db, feedback_id=feedback_id)


# Job Openings

@app.post("/jobs/", response_model=schemas.JobOpening, summary="Criar vaga", description="Cria uma nova vaga de voluntariado. Requer autenticação.")
def create_job(
    job: schemas.JobOpeningCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    return crud.create_job_opening(db=db, job=job, user_id=current_user.id)


@app.get("/jobs/", response_model=list[schemas.JobOpening], summary="Listar vagas", description="Lista todas as vagas (pode filtrar por ativas).")
def read_jobs(
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    return crud.get_job_openings(db, skip=skip, limit=limit, active_only=active_only)


@app.get("/jobs/{job_id}", response_model=schemas.JobOpening, summary="Obter vaga", description="Retorna detalhes de uma vaga.")
def read_job(
    job_id: int, 
    db: Session = Depends(get_db)
):
    db_job = crud.get_job_opening(db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job opening not found")
    return db_job


@app.put("/jobs/{job_id}", response_model=schemas.JobOpening, summary="Atualizar vaga", description="Atualiza uma vaga existente. Requer autenticação.")
def update_job(
    job_id: int, 
    job: schemas.JobOpeningCreate, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_job = crud.update_job_opening(db, job_id=job_id, job=job)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job opening not found")
    return db_job


@app.delete("/jobs/{job_id}", response_model=schemas.JobOpening, summary="Deletar vaga", description="Deleta uma vaga existente. Requer autenticação.")
def delete_job(
    job_id: int, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_active_user)
):
    db_job = crud.delete_job_opening(db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job opening not found")
    return db_job


# Job Applications

@app.post("/jobs/apply", response_model=schemas.JobApplication, summary="Candidatar-se a uma vaga", description="Candidata-se a uma vaga usando email já cadastrado.")
def apply_for_job(
    job_id: int,
    email: str,
    db: Session = Depends(get_db)
):
    # 1. Check if volunteer exists
    volunteer = crud.get_volunteer_by_email(db, email=email)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Email não encontrado. Cadastre-se como voluntário primeiro.")
    
    # 2. Check if job exists and is active
    job = crud.get_job_opening(db, job_id=job_id)
    if not job or not job.is_active:
         raise HTTPException(status_code=404, detail="Vaga não encontrada ou inativa.")

    # 3. Apply
    application_data = schemas.JobApplicationCreate(job_id=job_id, volunteer_id=volunteer.id)
    return crud.create_job_application(db, application_data)


@app.get("/jobs/{job_id}/applications", response_model=list[schemas.JobApplication], summary="Listar candidaturas", description="Lista candidaturas de uma vaga. Requer autenticação.")
def read_job_applications(
    job_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    return crud.get_job_applications(db, job_id=job_id, skip=skip, limit=limit)