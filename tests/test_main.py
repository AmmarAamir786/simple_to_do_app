#lifecycle of a test
    #1- Gathering resources: Table, Session, Client
    #2- Act
    #3- Assert
    #4- Cleanup

#step1: add the following packages
    #poetry add pytest
    #poetry add httpx

from fastapi.testclient import TestClient
from fastapi import FastAPI
from simple_to_do_app import setting
from sqlmodel import SQLModel, create_engine, Session
from simple_to_do_app.main import app, get_session
import pytest

#step2: create engine
    #new engine will be made because here instead of databaseurl we will be using testdatabaseurl
connection_string: str = str(setting.TEST_DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode":"require"}, pool_recycle=300, pool_size=10, echo=True) 

#step3: Creating Fixtures
    #Task of fixtures: Automate Arrange and Cleanup process
@pytest.fixture(scope="module", autouse=True) #module= fixture will run for our whole module(test file) before the first test and will clean up after all the tests ends. Autouse= Every test will automatically call this
def get_db_session():
    SQLModel.metadata.create_all(engine) #creating the table
    yield Session(engine) #creating session

@pytest.fixture(scope="function")
def test_app(get_db_session):
    def test_session(): #depedency overide for the session coming from the main file
        yield get_db_session
    app.dependency_overrides[get_session] = test_session
    with TestClient(app=app) as client:
        yield client

#step4: testing the functions we made in our main file
    #to run the test = poetry run pytest

#testing the get request
def test_root():
    client = TestClient(app=app) #the name of our app
    response = client.get("/")
    data = response.json() #getting back the response
    assert response.status_code == 200 #this will evaluate the funtion and will return either true or false. in case of false, assert will raise an assert exception error
    assert data == {"message" : "Welcome. This is not your first time here :)"} #this needs to be the same as the main file

#testing post request
def test_create_todo(test_app):
    test_todo  = {"content" : "Create Todo Test", "is_completed" : False}
    response = test_app.post('/todos/', json= test_todo)
    data = response.json()
    assert response.status_code == 200
    assert data["content"] == test_todo["content"]

#testing getting all the todos
def test_get_all(test_app):
    #writing this to post a new todo and then getting it back from the server to see if it works
    test_todo  = {"content": "get all todos test", "is_completed" : False}
    response = test_app.post('/todos/', json=test_todo)
    data = response.json()

    response = test_app.get('/todos/')
    new_todo = response.json()[-1] #getting a list of todos. And since we need the newly added item we will need the last item from our list
    assert response.status_code == 200
    assert new_todo["content"] == test_todo["content"]

#testing getting a single todo
def test_get_single_todo(test_app):
    #writing this to post a new todo and then getting it back from the server to see if it works
    test_todo  = {"content": "get single todo test", "is_completed" : False}
    response = test_app.post('/todos/', json=test_todo)
    todo_id = response.json()["id"]

    response = test_app.get(f'/todos/{todo_id}')
    data = response.json()
    assert response.status_code == 200
    assert data["content"] == test_todo['content']

#testing editing the existing todo
def test_edit_todo(test_app):
    #writing this to post a new todo and then getting it back from the server to see if it works
    test_todo = {"content":"edit todo test", "is_completed":False}
    response = test_app.post('/todos/',json=test_todo)
    todo_id = response.json()["id"]

    edited_todo = {"content":"We have edited this", "is_completed":False}
    response = test_app.put(f'/todos/{todo_id}',json=edited_todo)
    data = response.json()
    assert response.status_code == 200
    assert data["content"] == edited_todo["content"]

#testing deleting the existing todo
def test_delete_todo(test_app):
    #writing this to post a new todo and then getting it back from the server to see if it works
    test_todo  = {"content":"delete single todo test", "is_completed" : False}
    response = test_app.post('/todos/', json=test_todo)
    todo_id = response.json()["id"]

    response = test_app.delete(f'/todos/{todo_id}')
    data = response.json()
    assert response.status_code == 200
    assert data["message"] == "Task successfully deleted"

#If we dont add fixtures we would have to add the following code in every test except the root test
    # SQLModel.metadata.create_all(engine) #creating table
    # with Session(engine) as session: #creating session
    #     def db_session_override(): #depedency overide for the session coming from the main file is using the main branch db url. We need to override it
    #         return session
    # app.dependency_overrides[get_session] = db_session_override #dictionary provided by fastapi to override our existing session
    # client = TestClient(app=app)


    # test_todo  = {"content": "Create Todo Test", "is_completed" : False}
    # response = client.post('/todos/', json= test_todo)
    # data = response.json()
    # assert response.status_code == 200
    # assert data["content"] == test_todo["content"]