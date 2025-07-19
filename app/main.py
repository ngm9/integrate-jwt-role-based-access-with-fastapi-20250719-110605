import os
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

# Config
SECRET_KEY = os.getenv("JWT_SECRET", "WRONG_SECRET_KEY")  # <-- This was previously misconfigured!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Models
class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class User(BaseModel):
    username: str
    role: str

fake_users_db = {
    "alice": {"username": "alice", "role": "admin"},
    "bob": {"username": "bob", "role": "user"},
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI()

# Middleware to extract "Authorization: Bearer ..." and attach to request state
class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            request.state.token = auth.split(" ", 1)[1]
        else:
            request.state.token = None
        response = await call_next(request)
        return response

app.add_middleware(JWTAuthMiddleware)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    # Use correct secret key and algorithm
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token payload",
            )
        token_data = TokenData(username=username, role=role)
        return token_data
    except JWTError as e:
        print(f"JWT decode failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

def get_current_user(request: Request):
    token = request.state.token
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token_data = verify_token(token)
    user_dict = fake_users_db.get(token_data.username)
    if not user_dict or user_dict["role"] != token_data.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User mismatch",
        )
    return User(**user_dict)

@app.post("/token")
async def login_for_access_token(form_data: dict):
    username = form_data.get("username")
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
        )
    # For demo, all users are valid
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}

@app.get("/admin")
async def get_admin_resource(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return {"msg": "Welcome, admin %s!" % current_user.username}
