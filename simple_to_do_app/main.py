#step 1: poetry add fastapi unicorn sqlmodel psycopg[binary]
#step 2: create neon postgresql account and server

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel, Session, select
from typing import Annotated
from contextlib import asynccontextmanager
from simple_to_do_app import settings

#step 3: Create Model for todo
   # Data Model = just for validating data
   # Table Model = for creating a table
   # SQL Model = for both creating and validating

class Todo (SQLModel, table=True): #validating and creating the table
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(index=True, min_length=5, max_length=200) #an index on a db column allows the db to efficiently locate rows with matching values
    is_completed: bool = Field(default=False)
    
#step 4: connect our app with dp 
#step 5: create .env file on root
#step 6: create setting.py file

#step 7: Create Engine
    # Engine is used to establish the connection between our app and our db (neon)
    # Engine is one for whole application
    # Psycopg translates Python code and data structures into commands and data formats that PostgreSQL understands, enabling seamless interaction between your application and the database.
connection_string: str = str(settings.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode":"require"}, pool_recycle=300, pool_size=10, echo=True) 
    #sslmode will make the connection secure. Echo shows all the steps performed in the terminal

#step 8: create tables
def create_tables():
    SQLModel.metadata.create_all(engine)

#step 9: create session
    # for every fuction/transaction there will be a new session
    # E.g for every new logged in user, a new session is made
    # when user logs out, session closes
    # we are creating our session in a generator function so it closes the session automatically whenever we dont need it
def get_session():
    with Session(engine) as session:
        yield session

#step 10: create a context manager that will run right as when the app starts up. Here the first thing the app will do is create the tables
@asynccontextmanager
async def lifespan(app:FastAPI, title="Fight Your Dementia", version="1.0.0"):
    print("Creating Tables")
    create_tables()
    print("Tables Created")
    yield

#step 11: create desired http methods

app : FastAPI = FastAPI(lifespan=lifespan)

@app.get('/')
async def root():
    return {"message" : "Welcome. This is not your first time here :)"}

@app.post('/todos/', response_model=Todo) #response model is used to validate the data
async def create_todo(todo:Todo, session:Annotated[Session, Depends(get_session)]): #todo is data given by the user. session is where we are injecting our depedency
    session.add(todo) #saves in memory not in db
    session.commit() #this will create data in db. commit also removes the data from the variables
    session.refresh(todo)   
    return todo

@app.get('/todos/', response_model=list[Todo])
async def get_all(session:Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo)).all()
    if todos:
        return todos
    else:
        raise HTTPException (status_code=404, detail="Tasks does not exist.")

@app.get('/todos/{id}', response_model=Todo)
async def get_single_todo(id: int, session:Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id==id)).first()
    if todo:
        return todo
    else:
        raise HTTPException(status_code=404, detail="Task with the given ID does not exist.")
        
@app.put('/todos/{id}')
async def edit_todo(id: int, todo: Todo, session: Annotated[Session, Depends(get_session)]):
    existing_todo = session.exec(select(Todo).where(Todo.id == id)).first()
    if existing_todo:
        existing_todo.content = todo.content
        existing_todo.is_completed = todo.is_completed
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException(status_code=404, detail="No task found")

@app.delete('/todos/{id}')
async def delete_todo(id: int, session: Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id==id)).first()
    if todo:
        session.delete(todo)
        session.commit()
        #session.refresh(todo)
        return {"message" : "Task successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail="Task with the given ID does not exist.")