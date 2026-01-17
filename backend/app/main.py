from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.router import api_router
from dotenv import load_dotenv
load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Platform Builder",
        version="2.0.0",
        description="Advanced Modular AI Builder Backend"
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all routes
    app.include_router(api_router)

    @app.get("/health")
    def health_check():
        return {"status": "online", "version": "2.0.0"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Now we run the app string path
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
    #  For running the backend use any one of below comand from backend directory
        # # Windows
        # python -m app.main

        # # Or using uvicorn directly
        # uvicorn app.main:app --reload