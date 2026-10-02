import time
from contextlib import asynccontextmanager
 
import aiosqlite
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
 
 
def load_model():
    print("⏳ กำลังโหลดโมเดล ML ... (3 วินาที)")
    time.sleep(3)
    print("✅ โหลดโมเดลเสร็จ")
    return lambda x: x * 42.0
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== STARTUP =====
    print("🚀 [STARTUP] เริ่มเตรียมระบบ")
    app.state.model = load_model()

 
    db = await aiosqlite.connect("app.db")
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_val REAL,
            result_val REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    await db.commit()
    app.state.db = db
    print("[STARTUP] เชื่อมต่อ SQLite (app.db) สำเร็จ")
 
    try:
        yield
    finally:
        # ===== SHUTDOWN =====
        print("🛑 [SHUTDOWN] กำลังปิดระบบ")
        app.state.model = None
        if hasattr(app.state, "db") and app.state.db:
            await db.close()
        print("🔒 [SHUTDOWN] ปิด Database และเคลียร์โมเดลแล้ว")


 
app = FastAPI(title="Lifespan Demo", lifespan=lifespan)
 
 
class PredictIn(BaseModel):
    x: float
 
 
@app.get("/")
async def root():
    return {
        "status": "online",
        "model_loaded": app.state.model is not None,
        "db_connected": app.state.db is not None,
    }
 
 
@app.post("/predict")
async def predict(body: PredictIn):
    model = app.state.model
    if model is None:
        raise HTTPException(status_code=503, detail="โมเดลยังไม่พร้อม")
    result = model(body.x)
 
    await app.state.db.execute(
        "INSERT INTO prediction_logs (input_val, result_val) VALUES (?, ?)",
        (body.x, result),
    )
    await app.state.db.commit()
    return {"input": body.x, "prediction": result}
 
 
@app.get("/logs")
async def get_logs():
    async with app.state.db.execute(
        "SELECT id, input_val, result_val, created_at "
        "FROM prediction_logs ORDER BY id DESC"
    ) as cursor:
        rows = await cursor.fetchall()
    logs = [
        {"id": r[0], "input": r[1], "result": r[2], "created_at": r[3]}
        for r in rows
    ]
    return {"total": len(logs), "logs": logs}

@app.on_event("startup")
async def old_style_startup():
    print("👴 [OLD] startup แบบเก่า")
