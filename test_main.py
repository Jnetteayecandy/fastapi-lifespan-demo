from fastapi.testclient import TestClient
from main import app
 
 
# ต้องวางไว้ก่อนเทสต์ตัวที่ 2 (ดูหมายเหตุด้านล่าง)
def test_without_with_lifespan_does_not_run():
    client = TestClient(app, raise_server_exceptions=False)
    r = client.post("/predict", json={"x": 2})
    assert r.status_code == 500  # ไม่มี STARTUP จึงไม่มี app.state.model
 
 
def test_with_lifespan_runs():
    with TestClient(app) as client:  # เข้า with = STARTUP / ออก = SHUTDOWN
        r = client.post("/predict", json={"x": 2})
        assert r.status_code == 200
        assert r.json()["prediction"] == 84.0
