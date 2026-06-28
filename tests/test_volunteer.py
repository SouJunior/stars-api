import pytest
from faker import Faker
from app import models

_fake = Faker("pt_BR")


def make_payload(**overrides) -> dict:
    return {
        "name": _fake.name(),
        "linkedin": f"https://linkedin.com/in/{_fake.user_name()}",
        "email": _fake.unique.email(),
        "is_active": True,
        "jobtitle_id": 1,
        **overrides,
    }


@pytest.fixture
def jobtitle(db):
    jt = models.JobTitle(title="Backend Developer", is_active=True)
    db.add(jt)
    db.commit()
    db.refresh(jt)
    return jt


# ──────────────────────────────────────────────
# Success
# ──────────────────────────────────────────────

class TestCreateVolunteerSuccess:
    def test_returns_200(self, client, jobtitle):
        response = client.post("/volunteer", json=make_payload(jobtitle_id=jobtitle.id))
        assert response.status_code == 200

    def test_response_contains_id(self, client, jobtitle):
        data = client.post("/volunteer", json=make_payload(jobtitle_id=jobtitle.id)).json()
        assert isinstance(data["id"], int)

    def test_response_fields_match_input(self, client, jobtitle):
        p = make_payload(jobtitle_id=jobtitle.id)
        data = client.post("/volunteer", json=p).json()
        assert data["name"] == p["name"]
        assert data["linkedin"] == p["linkedin"]
        assert data["jobtitle_id"] == jobtitle.id
        assert data["is_active"] is True

    def test_masked_email_in_response(self, client, jobtitle):
        data = client.post("/volunteer", json=make_payload(jobtitle_id=jobtitle.id)).json()
        assert "masked_email" in data

    def test_two_different_emails_both_succeed(self, client, jobtitle):
        r1 = client.post("/volunteer", json=make_payload(jobtitle_id=jobtitle.id))
        r2 = client.post("/volunteer", json=make_payload(jobtitle_id=jobtitle.id))
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] != r2.json()["id"]


# ──────────────────────────────────────────────
# Business-rule validation (400)
# ──────────────────────────────────────────────

class TestCreateVolunteerBusinessErrors:
    def test_duplicate_email_returns_400(self, client, jobtitle):
        p = make_payload(jobtitle_id=jobtitle.id)
        client.post("/volunteer", json=p)
        response = client.post("/volunteer", json=p)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_duplicate_email_different_name_still_400(self, client, jobtitle):
        p = make_payload(jobtitle_id=jobtitle.id)
        client.post("/volunteer", json=p)
        response = client.post("/volunteer", json={**p, "name": _fake.name()})
        assert response.status_code == 400

    def test_jobtitle_id_zero_returns_400(self, client):
        response = client.post("/volunteer", json=make_payload(jobtitle_id=0))
        assert response.status_code == 400
        assert response.json()["detail"] == "We need jobtitle_id"

    def test_jobtitle_id_negative_returns_400(self, client):
        response = client.post("/volunteer", json=make_payload(jobtitle_id=-1))
        assert response.status_code == 400
        assert response.json()["detail"] == "We need jobtitle_id"

    def test_jobtitle_id_large_negative_returns_400(self, client):
        response = client.post("/volunteer", json=make_payload(jobtitle_id=-999))
        assert response.status_code == 400
        assert response.json()["detail"] == "We need jobtitle_id"


# ──────────────────────────────────────────────
# Schema validation (422)
# ──────────────────────────────────────────────

class TestCreateVolunteerSchemaValidation:
    def test_missing_name_returns_422(self, client, jobtitle):
        p = {k: v for k, v in make_payload(jobtitle_id=jobtitle.id).items() if k != "name"}
        assert client.post("/volunteer", json=p).status_code == 422

    def test_missing_linkedin_returns_422(self, client, jobtitle):
        p = {k: v for k, v in make_payload(jobtitle_id=jobtitle.id).items() if k != "linkedin"}
        assert client.post("/volunteer", json=p).status_code == 422

    def test_missing_email_returns_422(self, client, jobtitle):
        p = {k: v for k, v in make_payload(jobtitle_id=jobtitle.id).items() if k != "email"}
        assert client.post("/volunteer", json=p).status_code == 422

    def test_missing_jobtitle_id_returns_422(self, client, jobtitle):
        p = {k: v for k, v in make_payload(jobtitle_id=jobtitle.id).items() if k != "jobtitle_id"}
        assert client.post("/volunteer", json=p).status_code == 422

    def test_empty_body_returns_422(self, client):
        assert client.post("/volunteer", json={}).status_code == 422

    def test_jobtitle_id_string_returns_422(self, client):
        response = client.post("/volunteer", json=make_payload(jobtitle_id="abc"))
        assert response.status_code == 422
