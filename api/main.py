import os
from typing import Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from test import router as voice_router

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="Syfo AI — Strategy Booking API", version="1.0.0")

_cors_origins = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in _cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)

DB_HOST="database-1.cqhcysao051z.us-east-1.rds.amazonaws.com"
DB_PORT=5432
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="Prasanth001"
def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


class StrategyBooking(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    monthly_revenue: Optional[str] = None
    biggest_challenge: Optional[str] = None
    preferred_call_time: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/book-strategy", status_code=201)
def book_strategy(booking: StrategyBooking):
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO strategy_bookings
                (full_name, email, phone, company_name, industry,
                 monthly_revenue, biggest_challenge, preferred_call_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (
                booking.full_name,
                booking.email,
                booking.phone,
                booking.company_name,
                booking.industry,
                booking.monthly_revenue,
                booking.biggest_challenge,
                booking.preferred_call_time,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return {
            "success": True,
            "message": "Booking confirmed! We'll be in touch within 24 hours.",
            "id": row["id"],
            "created_at": str(row["created_at"]),
        }
    except psycopg2.Error as db_err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {db_err.pgerror}")
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if conn:
            conn.close()


@app.get("/api/bookings")
def list_bookings(limit: int = 50, offset: int = 0):
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, full_name, email, phone, company_name, industry,
                   monthly_revenue, biggest_challenge, preferred_call_time,
                   status, created_at
            FROM strategy_bookings
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
        cur.close()
        return {"success": True, "total": len(rows), "bookings": [dict(r) for r in rows]}
    except psycopg2.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {db_err.pgerror}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
    )
