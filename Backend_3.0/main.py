from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel, validator
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse

# Configuración de Base de Datos
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()



# 🔐 Configuración de Seguridad 🔐
SECRET_KEY = "supersecreto123"  # Cámbialo por una clave más segura
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



# 🛡️ Configuración de CORS (Restringido al frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia esto según tu frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)



# 🔒 Funciones de seguridad 🔒
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")



# 🛢️ Modelos de Base de Datos
class Administrador(Base):
    __tablename__ = "administradores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    contrasena = Column(String)

class Camara(Base):
    __tablename__ = "camaras"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    nombre_wifi = Column(String, index=True)
    contrasena_wifi = Column(String)
    direccion_url = Column(String)
    horarios = relationship("Horario", back_populates="camara")
    pacientes = relationship("Paciente", back_populates="camara")

class Horario(Base):
    __tablename__ = "horarios"
    id = Column(Integer, primary_key=True, index=True)
    dia = Column(String, index=True)
    hora_inicio = Column(String)
    hora_termino = Column(String)
    camara_id = Column(Integer, ForeignKey("camaras.id"))
    camara = relationship("Camara", back_populates="horarios")

class Paciente(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    rut = Column(String, index=True)
    dia_ingreso = Column(String, index=True)
    hora_ingreso = Column(String, index=True)
    id_camara = Column(Integer, ForeignKey("camaras.id"))
    camara = relationship("Camara", back_populates="pacientes")

Base.metadata.create_all(bind=engine)



# 📜 Schemas de Pydantic con validaciones
class AdministradorCreate(BaseModel):
    nombre: str
    contrasena: str

    @validator("contrasena")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return value

class CamaraCreate(BaseModel):
    nombre: str
    nombre_wifi: str
    contrasena_wifi: str
    direccion_url: str

class HorarioCreate(BaseModel):
    dia: str
    hora_inicio: str
    hora_termino: str
    camara_id: int

class PacienteCreate(BaseModel):
    nombre: str
    rut: str
    dia_ingreso: str
    hora_ingreso: str
    id_camara: int



# 🛠️ Dependencia para obtener la sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# 🔑 Endpoint para autenticación y generación de tokens
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_admin = db.query(Administrador).filter(Administrador.nombre == form_data.username).first()
    if not db_admin or not verify_password(form_data.password, db_admin.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    access_token = create_access_token(data={"sub": db_admin.nombre}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}



# 🛡️ Rutas protegidas con autenticación JWT
@app.post("/admin/")
def create_admin(admin: AdministradorCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    hashed_password = hash_password(admin.contrasena)
    db_admin = Administrador(nombre=admin.nombre, contrasena=hashed_password)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

@app.get("/admin/{admin_nombre}")
def get_admin(admin_nombre: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_admin = db.query(Administrador).filter(Administrador.nombre == admin_nombre).first()
    if not db_admin:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    return db_admin

@app.delete("/admin/{admin_id}")
def delete_admin(admin_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_admin = db.query(Administrador).filter(Administrador.id == admin_id).first()
    if not db_admin:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    db.delete(db_admin)
    db.commit()
    return {"message": "Administrador eliminado"}



# 🎥 Rutas CRUD para Cámaras
@app.post("/camara/")
def create_camara(camara: CamaraCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_camara = Camara(nombre=camara.nombre, nombre_wifi=camara.nombre_wifi, contrasena_wifi=camara.contrasena_wifi, direccion_url=camara.direccion_url)
    db.add(db_camara)
    db.commit()
    db.refresh(db_camara)
    return db_camara

@app.get("/camara/")
def get_all_camaras(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(Camara).all()

@app.get("/camara/{camara_id}")
def get_camara(camara_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_camara = db.query(Camara).filter(Camara.id == camara_id).first()
    if not db_camara:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    return db_camara

@app.delete("/camara/{camara_id}")
def delete_camara(camara_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_camara = db.query(Camara).filter(Camara.id == camara_id).first()
    if not db_camara:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    db.delete(db_camara)
    db.commit()
    return {"message": "Cámara eliminada"}

@app.put("/camara/{camara_id}")
def update_camara(camara_id: int, camara_data: dict, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_camara = db.query(Camara).filter(Camara.id == camara_id).first()
    
    if not db_camara:
        raise HTTPException(status_code=404, detail="Camara no encontrada")

    # Actualizar los valores
    for key, value in camara_data.items():
        setattr(db_camara, key, value)

    db.commit()
    db.refresh(db_camara)

    return db_camara



# RUTAS CRUD PARA HORARIO
@app.post("/horario/")
def create_horario(horario: HorarioCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_horario = Horario(dia=horario.dia, hora_inicio=horario.hora_inicio, hora_termino=horario.hora_termino, camara_id=horario.camara_id)
    db.add(db_horario)
    db.commit()
    db.refresh(db_horario)
    return db_horario

@app.delete("/horario/{horario_id}")
def delete_horario(horario_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_horario = db.query(Horario).filter(Horario.id == horario_id).first()
    if not db_horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    db.delete(db_horario)
    db.commit()
    return {"message": "Horario eliminado"}

@app.get("/horario/{horario_id}")
def get_horario(horario_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_horario = db.query(Horario).filter(Horario.id == horario_id).first()
    if not db_horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    return db_horario

@app.get("/horario/")
def get_all_horarios(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    horarios = db.query(Horario).all()
    return horarios

@app.get("/horario/camara/{camara_id}")
def get_horarios_por_camara(camara_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    horarios = db.query(Horario).filter(Horario.camara_id == camara_id).all()
    return horarios

@app.put("/horario/{horario_id}")
def update_horario(horario_id: int, horario_data: dict, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_horario = db.query(Horario).filter(Horario.id == horario_id).first()
    
    if not db_horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    # Actualizar los valores
    for key, value in horario_data.items():
        setattr(db_horario, key, value)

    db.commit()
    db.refresh(db_horario)

    return db_horario


# RUTAS CRUD PARA PACIENTES
@app.post("/paciente/")
def create_paciente(paciente: PacienteCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    # Verifica si ya existe un paciente con el mismo RUT y la misma fecha
    existe = db.query(Paciente).filter(
        Paciente.rut == paciente.rut,
        Paciente.dia_ingreso == paciente.dia_ingreso
    ).first()

    if existe:
        raise HTTPException(status_code=400, detail="El paciente ya fue registrado hoy.")

    nuevo_paciente = Paciente(
        nombre=paciente.nombre,
        rut=paciente.rut,
        dia_ingreso=paciente.dia_ingreso,
        hora_ingreso=paciente.hora_ingreso,
        id_camara=paciente.id_camara
    )
    db.add(nuevo_paciente)
    db.commit()
    db.refresh(nuevo_paciente)
    return nuevo_paciente

@app.get("/paciente/{paciente_rut}")
def get_paciente(paciente_rut: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_paciente = db.query(Paciente).filter(Paciente.rut == paciente_rut).first()
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return db_paciente

@app.get("/paciente/")
def get_all_pacientes(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    pacientes = db.query(Paciente).all()
    return pacientes

@app.delete("/paciente/{paciente_rut}/{dia_ingreso}")
def delete_paciente(paciente_rut: str, dia_ingreso: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    db_paciente = db.query(Paciente).filter(
        Paciente.rut == paciente_rut,
        Paciente.dia_ingreso == dia_ingreso
    ).first()
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado para ese día")
    
    db.delete(db_paciente)
    db.commit()
    return {"message": "Paciente eliminado"}

@app.get("/paciente/ultimos6/{camara_id}")
def get_last_6_pacientes(camara_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    pacientes = db.query(Paciente).filter(Paciente.id_camara == camara_id).order_by(desc(Paciente.id)).limit(6).all()
    return [{"nombre": p.nombre, "rut": p.rut, "hora_ingreso": p.hora_ingreso, "dia_ingreso": p.dia_ingreso} for p in pacientes]

@app.get("/pacientes/por-dia/{fecha}")
def get_pacientes_por_dia(fecha: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    pacientes = db.query(Paciente).filter(Paciente.dia_ingreso == fecha).order_by(Paciente.hora_ingreso).all()
    return JSONResponse(
        content=[{
            "nombre": p.nombre,
            "rut": p.rut,
            "dia_ingreso": p.dia_ingreso,
            "hora_ingreso": p.hora_ingreso
        } for p in pacientes]
    )

