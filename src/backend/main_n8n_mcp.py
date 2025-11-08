import uvicorn
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from starlette.middleware.cors import CORSMiddleware

from routers.gov_taxes_router import gov_taxes_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gov_taxes_router, prefix="/gov", tags=["gov"])

mcp = FastApiMCP(app)

mcp.mount_http()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
