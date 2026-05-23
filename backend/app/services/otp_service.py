import asyncio
import smtplib
import random
import string
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import TenantOTP
from app.core.config import settings

class OTPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_otp(self, length: int = 6) -> str:
        return "".join(random.choices(string.digits, k=length))

    async def create_otp(self, email: str = None, phone: str = None) -> str:
        otp_code = self.generate_otp()
        expired_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        query = select(TenantOTP).where(TenantOTP.verified == False)
        if email:
            query = query.where(TenantOTP.email == email)
        elif phone:
            query = query.where(TenantOTP.phone == phone)

        if email or phone:
            result = await self.db.execute(query)
            for existing_otp in result.scalars().all():
                existing_otp.verified = True

        # Create record
        otp_record = TenantOTP(
            email=email,
            phone=phone,
            otp_code=otp_code,
            expired_at=expired_at,
            verified=False
        )
        self.db.add(otp_record)
        await self.db.flush()
        return otp_code

    async def send_email_otp(self, email: str, otp_code: str):
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            raise ValueError("SMTP_USER and SMTP_PASSWORD are required to send OTP email")

        sender = settings.EMAIL_FROM or settings.SMTP_USER
        message = MIMEMultipart("alternative")
        message["Subject"] = "Mã xác thực OTP - NhaTro Manager"
        message["From"] = sender
        message["To"] = email
        message.attach(MIMEText(
            f"""
            <p>Xin chào,</p>
            <p>Mã OTP của bạn là: <strong>{otp_code}</strong>.</p>
            <p>Mã này có hiệu lực trong 5 phút.</p>
            """,
            "html",
            "utf-8",
        ))

        def send_mail():
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USER, [email], message.as_string())

        try:
            await asyncio.to_thread(send_mail)
            return {"message": "OTP email sent"}
        except Exception as e:
            raise Exception(f"Failed to send email via Gmail SMTP: {str(e)}") from e

    async def verify_otp(self, email: str = None, phone: str = None, otp_code: str = None) -> bool:
        # Find valid OTP
        query = select(TenantOTP).where(
            TenantOTP.otp_code == otp_code,
            TenantOTP.verified == False,
            TenantOTP.expired_at > datetime.now(timezone.utc)
        )
        if email:
            query = query.where(TenantOTP.email == email)
        elif phone:
            query = query.where(TenantOTP.phone == phone)
        else:
            return False

        result = await self.db.execute(query)
        otp_record = result.scalar_one_or_none()

        if otp_record:
            otp_record.verified = True
            await self.db.flush()
            return True
        return False
