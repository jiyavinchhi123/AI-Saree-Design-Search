import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.vision.feature_extractor import ColorInvariantFeatureExtractor
from app.vision.vector_index import SareeVectorIndex, VectorIndexManager
from app.onenote.graph_client import MicrosoftOneNoteClient
from app.routers import search, data_sources, designs, history

# Ensure data directories exist
os.makedirs("data/storage", exist_ok=True)
os.makedirs("data/indexes", exist_ok=True)

# Global services
extractor = ColorInvariantFeatureExtractor()
vector_index_mgr = VectorIndexManager()
vector_index = vector_index_mgr.get_index()
onenote_client = MicrosoftOneNoteClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import SessionLocal, UserRecord
    from app.seeder import run_auto_seed
    db = SessionLocal()
    try:
        run_auto_seed(db)
        user = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()
        if user:
            token = await onenote_client.get_valid_token_for_user(user.id, db)
            if token:
                print(f"[AI Saree Search] OneNote connected for: {user.display_name} ({user.email})")
            else:
                print(f"[AI Saree Search] OneNote registered for: {user.display_name} ({user.email}), awaiting token refresh.")
    except Exception as e:
        print(f"[AI Saree Search] Lifespan initialization notice: {e}")
    finally:
        db.close()

    print(f"[AI Saree Search] Server started. Loaded {vector_index_mgr.count()} indexed OneNote designs.")

    yield


app = FastAPI(
    title="AI Saree Design Search API",
    description="Enterprise Vision AI for OneNote Saree Design Retrieval with Color-Invariant Matching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS: Allow exact Vercel production domain, Vercel preview domains, and localhost for dev
allowed_origins = [
    "https://ai-saree-design-search.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]
frontend_env = os.getenv("FRONTEND_URL", "").strip()
if frontend_env and frontend_env not in allowed_origins:
    allowed_origins.append(frontend_env.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve stored images and structural previews
app.mount("/api/storage", StaticFiles(directory="data/storage"), name="storage")

# Include Routers
app.include_router(search.router)
app.include_router(data_sources.router)
app.include_router(designs.router)
app.include_router(history.router)

# Route alias for /api/onenote/auth/callback
app.add_api_route("/api/onenote/auth/callback", data_sources.auth_callback, methods=["GET"], tags=["Data Sources"])

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Saree Design Search",
        "total_indexed_designs": vector_index_mgr.count(),
        "color_invariant_engine": "DINOv2 (ViT-B/14) Structural Motif Embeddings",
        "vector_search": "FAISS IndexFlatIP (Cosine Similarity)"
    }

# Mount static web frontend
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

