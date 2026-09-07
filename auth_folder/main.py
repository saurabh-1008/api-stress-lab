from fastapi import FastAPI,HTTPException
from db import add_user,auth_user
from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str

app=FastAPI()

@app.post("/register")
def register(user:User):
    try:
        add_user(user.username,user.password)
        return {"message":"User registered successfully"}
    except Exception as e:
        return {"error":str(e)}

@app.get("/login")
def login(username:str,password:str):
    try:
        if auth_user(username,password):
            return{"message":"User authenticated successfully"}
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )