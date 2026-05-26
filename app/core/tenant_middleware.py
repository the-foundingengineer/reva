import os
import jwt
import contextvars
from fastapi import Request
from app.core.logger import get_logger

logger = get_logger(__name__)

# Context variable used securely store the tenant JWT for the current async request.
tenant_token_var = contextvars.ContextVar('tenant_token', default=None)

class TenantMiddleware:
    def __init__(self, app):
        self.app = app
        
        # We need a secret to sign custom auth tokens for PostgREST
        self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "super-secret-jwt-token-replace-in-prod")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        request = Request(scope, receive=receive)
        
        # 1. Determine Tenant 
        # Typically from x-tenant-id header naturally sent by the NextJS frontend 
        # Or derived from the webhook payload in gateway URL params e.g ?tenant_id=...
        tenant_id = request.headers.get("x-tenant-id") or request.query_params.get("tenant_id")
        
        if tenant_id:
            logger.info(f"Tenant Context Set: {tenant_id}")
            # 2. Sign a valid Supabase JWT that includes the tenant_id in its claims
            token = jwt.encode({
                "role": "authenticated", # This enables Postgres Authenticated Role
                "tenant_id": tenant_id,  # This maps to auth.jwt() ->> 'tenant_id' in RLS
                "iss": "supabase"
            }, self.jwt_secret, algorithm="HS256")
            
            # 3. Store the JWT in the ContextVar.
            # Downstream get_supabase() will detect this and append it as a Header.
            tenant_token_var.set(token)
        
        # Continue execution
        await self.app(scope, receive, send)
