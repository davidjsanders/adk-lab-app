import os
from dotenv import load_dotenv
from app.classes.settings import Settings

# Populate environment
load_dotenv(override=False)

settings = Settings()

# Apply Service Account Impersonation for local development if IMPERSONATE_SA is set
if settings.impersonate_sa:
    import google.auth
    from google.auth.impersonated_credentials import Credentials
    
    # Only impersonate in local workstation development environments
    if not os.getenv("K_SERVICE") and not os.getenv("APP_URL"):
        original_default = google.auth.default
        def impersonated_default(*args, **kwargs):
            base_creds, project = original_default(*args, **kwargs)
            impersonated_creds = Credentials(
                source_credentials=base_creds,
                target_principal=settings.impersonate_sa,
                target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            return impersonated_creds, project
        google.auth.default = impersonated_default

