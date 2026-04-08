from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from onelogin.saml2.auth import OneLogin_Saml2_Auth

from app.core.auth import get_saml_settings, prepare_saml_request, create_jwt_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _init_saml_auth(request: Request) -> OneLogin_Saml2_Auth:
    req = prepare_saml_request(request)
    saml_settings = get_saml_settings(request)
    return OneLogin_Saml2_Auth(req, saml_settings)


@router.get("/saml/login")
async def saml_login(request: Request):
    """Initiate SAML SSO login - redirect to IdP."""
    auth = _init_saml_auth(request)
    sso_url = auth.login()
    return RedirectResponse(url=sso_url)


@router.post("/saml/acs")
async def saml_acs(request: Request):
    """SAML Assertion Consumer Service - process IdP response."""
    auth = _init_saml_auth(request)

    form_data = await request.form()
    req = prepare_saml_request(request)
    req["post_data"] = dict(form_data)

    auth = OneLogin_Saml2_Auth(req, get_saml_settings(request))
    auth.process_response()

    errors = auth.get_errors()
    if errors:
        raise HTTPException(status_code=400, detail=f"SAML Error: {', '.join(errors)}")

    if not auth.is_authenticated():
        raise HTTPException(status_code=401, detail="SAML authentication failed")

    attributes = auth.get_attributes()
    name_id = auth.get_nameid()

    token = create_jwt_token({
        "sub": name_id,
        "email": name_id,
        "name": attributes.get("displayName", [name_id])[0],
        "department": attributes.get("department", [None])[0],
    })

    # Redirect to frontend with token
    return RedirectResponse(url=f"http://localhost:3000/auth/callback?token={token}")


@router.get("/saml/slo")
async def saml_slo(request: Request):
    """Initiate Single Logout."""
    auth = _init_saml_auth(request)
    slo_url = auth.logout()
    return RedirectResponse(url=slo_url)


@router.get("/saml/metadata")
async def saml_metadata(request: Request):
    """SP metadata for IdP registration."""
    auth = _init_saml_auth(request)
    metadata = auth.get_settings().get_sp_metadata()
    errors = auth.get_settings().validate_metadata(metadata)
    if errors:
        raise HTTPException(status_code=500, detail=f"Metadata error: {', '.join(errors)}")
    return metadata
