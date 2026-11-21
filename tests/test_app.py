from backend import create_app
from backend.extensions import db
def test_register_and_checklist():
    app=create_app({"TESTING":True,"SQLALCHEMY_DATABASE_URI":"sqlite://","SECRET_KEY":"test-secret","ALLOW_REGISTRATION":True})
    client=app.test_client()
    with app.app_context(): db.drop_all(); db.create_all()
    res=client.post("/api/auth/register",json={"email":"tester@example.com","password":"long-test-password","timezone":"Asia/Kolkata"})
    assert res.status_code==201
    routines=client.get("/api/routines").get_json()
    assert len(routines)>=4
    r=routines[0]
    assert client.put(f"/api/days/2026-11-21/completions/{r['id']}",json={"completed":True}).status_code==200
