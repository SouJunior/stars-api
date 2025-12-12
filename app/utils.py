from sqlalchemy.orm import Session
from app import models
import secrets
import logging
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def generate_edit_token():
    return secrets.token_urlsafe(32)

def send_edit_link_email(email: str, name: str, link: str):
    """
    Sends an email with the edit link via Brevo.
    """
    logger.info("========================================")
    logger.info(f"EMAIL TO: {email} (Name: {name})")
    logger.info(f"SUBJECT: Editar seu Perfil de Voluntário")
    logger.info(f"LINK: {link}")
    logger.info("========================================")
    print(f"Link de edição enviado para {email} (Name: {name}): {link}") # Ensure it prints to stdout for the user to see clearly in CLI

    if not os.getenv("BREVO_API_KEY"):
        logger.warning("BREVO_API_KEY not set, skipping actual email sending.")
        return True

    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = os.getenv("BREVO_API_KEY")

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email, "name": name}], # Pass name to 'to' field if template uses it
            template_id=10,
            params={"link_edit": link, "name": name},
            headers={
                "charset": "iso-8859-1",
            },
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)
        return True

    except ApiException as e:
        logger.error(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")
        return False