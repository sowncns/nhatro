import asyncio
import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import TenantOTP
from app.core.config import settings
import resend

class OTPService:
    def __init__(self, db: AsyncSession):
        self.db = db
        resend.api_key = settings.RESEND_API_KEY

    def generate_otp(self, length: int = 6) -> str:
        return "".join(random.choices(string.digits, k=length))

    async def create_otp(self, email: str = None, phone: str = None) -> str:
        otp_code = self.generate_otp()
        expired_at = datetime.now(timezone.utc) + timedelta(minutes=5)

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
        try:
            params = {
                "from": settings.EMAIL_FROM,
                "to": email,
                "subject": "Mã xác thực OTP - Tenant Portal",
                "html": f"<p>Mã OTP của bạn là: <strong>{otp_code}</strong>. Mã này có hiệu lực trong 5 phút.</p>",
            }
            # resend.Emails.send is synchronous, so we run it in a thread pool
            email_response = await asyncio.to_thread(resend.Emails.send, params)
            return email_response
        except Exception as e:
            raise Exception(f"Failed to send email via Resend: {str(e)}")

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
