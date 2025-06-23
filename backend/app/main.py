from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv # Added to load .env file for environment variables

# Load environment variables from .env file at the beginning
load_dotenv() # Searches for .env in the current directory (backend/)

from .database import connect_db, disconnect_db # Relative import
from .auth.routes import router as auth_router     # Relative import
from .analysis.routes import router as analysis_router # Relative import

app = FastAPI(
    title="SEENTIA API",
    version="1.0.0", # Added version
    description="SEENTIA - Your Personal AI Style Advisor API" # Added description
)

# Configure CORS
# IMPORTANT: For production, restrict allow_origins to your frontend's domain(s).
# Example: allow_origins=["https://www.seentia.app", "http://localhost:5173"] (for Vite dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - CHANGE FOR PRODUCTION
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Specify methods or use ["*"]
    allow_headers=["*"], # Allows all headers
)

@app.on_event("startup")
async def startup_event(): # Renamed for clarity, matches previous naming
    await connect_db()

@app.on_event("shutdown")
async def shutdown_event(): # Renamed for clarity
    await disconnect_db()

@app.get("/", tags=["Root"]) # Added tags for OpenAPI
def read_root():
    return {"message": "Welcome to the SEENTIA API"}

# Include routers with appropriate prefixes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["Analysis"]) # Prefix was /api/analysis, kept it.

# Optional: Health check endpoint
@app.get("/health", tags=["Health Check"])
async def health_check():
    # You can add more sophisticated health checks here, e.g., DB connectivity
    return {"status": "ok", "message": "SEENTIA API is healthy"}
