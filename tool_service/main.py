from fastapi import FastAPI

from database import Base, engine
from routers import products, orders, users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ecommerce Agent Tools API",
    description="Backend tools API for catalog and order-related agent queries.",
    version="1.0.0"
)

@app.get("/", tags=['Application'])
def health_check():
    return {
        "status": "ok",
        "message": "Ecommerce Agent Tools API is running"
    }

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(users.router)
