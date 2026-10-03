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
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        await onenote_client.load_tokens(db)
        if onenote_client.is_connected:
            print(f"[AI Saree Search] OneNote connected for: {onenote_client.user_profile.get('userPrincipalName') or onenote_client.user_profile.get('mail')}")
    except Exception as e:
        print(f"[AI Saree Search] OneNote token restore notice: {e}")
    finally:
        db.close()

    print(f"[AI Saree Search] Server started. Loaded {vector_index.count()} indexed OneNote designs.")
    yield

app = FastAPI(
    title="AI Saree Design Search API",
    description="Enterprise Vision AI for OneNote Saree Design Retrieval with Color-Invariant Matching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

