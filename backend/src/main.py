from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.apps.users.router import router as users_router
from src.apps.posts.router import router as posts_router
from src.apps.interactions.router import router as interactions_router
from src.apps.notifications.router import router as notifications_router
from src.apps.upload.router import router as upload_router
from src.apps.tags.router import router as tags_router

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")
    
    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"], # Add frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
    app.include_router(posts_router, prefix=f"{settings.API_V1_STR}/posts", tags=["posts"])
    app.include_router(interactions_router, prefix=f"{settings.API_V1_STR}/interactions", tags=["interactions"])
    app.include_router(notifications_router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
    app.include_router(upload_router, prefix=f"{settings.API_V1_STR}/upload", tags=["upload"])
    app.include_router(tags_router, prefix=f"{settings.API_V1_STR}/tags", tags=["tags"])
    
    @app.get("/")
    def read_root():
        return {"message": "Welcome to Lumen Park API"}
        
    return app

app = create_app()
