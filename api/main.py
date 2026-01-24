"""FastAPI application for Investigation Workbench API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import cases, events, entities, bookmarks, markers, search, graph, gaps

# Create FastAPI app
app = FastAPI(
    title="Investigation Workbench API",
    description="""
    REST API for the Investigation Workbench security investigation tool.

    Provides access to:
    - Case management and summaries
    - Event querying with multi-entity filtering
    - Entity exploration and relationships
    - Bookmarks and timeline markers
    - Search functionality
    - Entity relationship graphs
    - Coverage gap detection
    """,
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
        "http://localhost:8501",  # Streamlit
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cases.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(entities.router, prefix="/api")
app.include_router(bookmarks.router, prefix="/api")
app.include_router(markers.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(gaps.router, prefix="/api")


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.2.0"}


@app.get("/")
def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": "Investigation Workbench API",
        "docs": "/api/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
