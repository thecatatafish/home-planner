from typing import Annotated

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from database import get_session

templates = Jinja2Templates(directory="templates")
SessionDep = Annotated[Session, Depends(get_session)]
