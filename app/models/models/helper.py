from app.models.base import BaseModel,db  

class ProductType(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class PackageType(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    is_fragile = db.Column(db.Boolean(), nullable=False)

class TemperatureType(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    celcius = db.Column(db.String(10), nullable=False)

class AllocationType(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class SectorType(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class MovementType(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(5), nullable=False)

class DocumentType(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)


