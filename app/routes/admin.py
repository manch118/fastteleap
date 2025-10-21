from typing import Optional
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..settings import settings


router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(x_telegram_id: Optional[str] = Header(None, alias="X-Telegram-Id")) -> None:
    if x_telegram_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Telegram-Id header missing")
    try:
        telegram_id = int(x_telegram_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Telegram-Id header")
    if telegram_id != settings.admin_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/products", response_model=schemas.ProductOut, dependencies=[Depends(require_admin)])
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(
        title=payload.title,
        description=payload.description,
        price=payload.price,
        image=payload.image,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=schemas.ProductOut, dependencies=[Depends(require_admin)])
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.title is not None:
        product.title = payload.title
    if payload.description is not None:
        product.description = payload.description
    if payload.price is not None:
        product.price = payload.price
    if payload.image is not None:
        product.image = payload.image

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.delete(product)
    db.commit()
    return None


@router.post("/upload-image")
def upload_image(file: UploadFile = File(...), _: None = Depends(require_admin)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image uploads are allowed")

    # Resolve upload directory: <project>/test_app/static/uploads
    base_dir = Path(__file__).resolve().parents[2] / "static" / "uploads"
    base_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "").suffix or ".jpg"
    filename = f"{uuid4().hex}{ext}"
    filepath = base_dir / filename

    with filepath.open("wb") as f:
        f.write(file.file.read())

    url_path = f"/static/uploads/{filename}"
    return {"url": url_path}


