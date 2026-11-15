import hashlib
import hmac
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import AuditLog, GeneratedFile, PlanConfig, SessionLocal, User
from ai_orchestrator import process_engineering_request
from file_analyzer import analyze_uploaded_file, save_and_validate_upload
from surveying_calc import (
    adjust_closed_traverse_bowditch,
    latlon_to_utm,
    solve_differential_leveling,
)

router = APIRouter(prefix="/api/v1")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_and_increment_quota(db: Session, user: Optional[User]) -> dict:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    plan_code = user.plan_code if user else "free"
    plan = db.query(PlanConfig).filter_by(plan_code=plan_code).first()
    limit = plan.daily_requests_limit if plan else settings.FREE_DAILY_REQUESTS
    max_mb = plan.max_file_mb if plan else settings.FREE_MAX_FILE_MB

    if user:
        if user.last_usage_date != today:
            user.daily_used_count = 0
            user.last_usage_date = today
        if user.daily_used_count >= limit:
            raise HTTPException(status_code=429, detail=f"تم استهلاك الحد اليومي لباقتك ({limit} طلبات). قم بالترقية إلى Pro.")
        user.daily_used_count += 1
        db.commit()
        used = user.daily_used_count
    else:
        used = 1

    return {"plan": plan_code, "used_today": used, "daily_limit": limit, "max_file_mb": max_mb}


@router.get("/ai/quota")
def get_quota(db: Session = Depends(get_db)):
    plan = db.query(PlanConfig).filter_by(plan_code="free").first()
    return {
        "plan": "free",
        "used_today": 0,
        "daily_limit": plan.daily_requests_limit if plan else settings.FREE_DAILY_REQUESTS,
    }


@router.post("/ai/chat")
async def ai_chat_endpoint(
    message: str = Form(...),
    mode: str = Form("assistant"),
    session_id: str = Form("default"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    quota = check_and_increment_quota(db, user=None)
    file_analysis = None

    try:
        if file and file.filename:
            saved_path, ext = await save_and_validate_upload(file, max_mb=quota["max_file_mb"])
            file_analysis = analyze_uploaded_file(saved_path, ext)

        output = process_engineering_request(message=message, mode=mode, file_analysis=file_analysis)

        if output.get("artifact"):
            art = output["artifact"]
            db.add(GeneratedFile(filename=art["filename"], file_type=art["type"], file_path=art["download_url"]))

        db.add(AuditLog(action=f"ai_chat:{mode}", status="success", details=message[:200]))
        db.commit()

        return {
            "reply": output["reply"],
            "warnings": output["warnings"],
            "artifact": output["artifact"],
            "quota": quota,
        }
    except HTTPException:
        raise
    except Exception as exc:
        db.add(AuditLog(action=f"ai_chat:{mode}", status="error", details=str(exc)[:300]))
        db.commit()
        raise HTTPException(status_code=500, detail=f"خطأ في المعالجة الهندسية: {str(exc)}")


class LevelingRequest(BaseModel):
    initial_bm: float
    stations: List[dict]


class TraverseRequest(BaseModel):
    start_e: float
    start_n: float
    legs: List[dict]


@router.get("/calc/utm")
def api_latlon_to_utm(lat: float, lon: float):
    return latlon_to_utm(lat, lon)


@router.post("/calc/leveling")
def api_solve_leveling(req: LevelingRequest):
    return solve_differential_leveling(req.initial_bm, req.stations)


@router.post("/calc/traverse")
def api_adjust_traverse(req: TraverseRequest):
    return adjust_closed_traverse_bowditch(req.start_e, req.start_n, req.legs)


@router.put("/admin/plans/{plan_code}")
def admin_update_plan(
    plan_code: str,
    daily_requests_limit: int,
    max_file_mb: int,
    x_admin_secret: str = Header(...),
    db: Session = Depends(get_db),
):
    if x_admin_secret != settings.JWT_SECRET_KEY:
        raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل إعدادات الباقات.")
    plan = db.query(PlanConfig).filter_by(plan_code=plan_code).first()
    if not plan:
        raise HTTPException(status_code=404, detail="الباقة غير موجودة.")
    plan.daily_requests_limit = daily_requests_limit
    plan.max_file_mb = max_file_mb
    db.commit()
    return {"status": "updated", "plan": plan_code, "daily_requests_limit": daily_requests_limit, "max_file_mb": max_file_mb}


@router.post("/webhooks/payment")
async def real_payment_gateway_webhook(
    request: Request,
    x_webhook_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if not settings.PAYMENT_WEBHOOK_SECRET:
        raise HTTPException(status_code=501, detail="لم يتم ضبط مفتاح بوابة الدفع PAYMENT_WEBHOOK_SECRET بعد.")
    raw_body = await request.body()
    expected_sig = hmac.new(settings.PAYMENT_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, x_webhook_signature):
        raise HTTPException(status_code=401, detail="توقيع بوابة الدفع غير صالح.")

    payload = await request.json()
    user_email = payload.get("customer_email")
    if payload.get("status") == "paid" and user_email:
        user = db.query(User).filter_by(email=user_email).first()
        if user:
            user.plan_code = "pro"
            db.commit()
    return {"received": True}
