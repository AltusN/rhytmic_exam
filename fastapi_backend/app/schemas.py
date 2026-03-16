from pydantic import BaseModel, ConfigDict

class UserCreate(BaseModel):
    username: str
    name: str
    surname: str
    sagf_id: str
    email: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    name: str
    surname: str
    sagf_id: str
    email: str

    model_config = ConfigDict(from_attributes=True)