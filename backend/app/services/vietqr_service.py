"""VietQR Service - Generate QR codes for bank transfers"""
from typing import Optional
from urllib.parse import quote


class VietQRService:
    """Generate VietQR codes for Vietnamese bank transfers"""

    def __init__(self):
        self.base_url = "https://img.vietqr.io/image"

    def generate_qr_url(
        self,
        bank_code: str,
        account_number: str,
        amount: int,
        description: str,
        account_name: Optional[str] = None,
    ) -> str:
        """
        Generate VietQR URL

        Args:
            bank_code: Bank code (e.g., "970436" for Vietcombank)
            account_number: Bank account number
            amount: Amount in VND
            description: Transfer description
            account_name: Optional account holder name

        Returns:
            VietQR image URL
        """
        # Encode description for URL
        encoded_desc = quote(description)

        # Build URL
        url = f"{self.base_url}/{bank_code}-{account_number}-compact2.jpg"
        url += f"?amount={amount}"
        url += f"&addInfo={encoded_desc}"

        if account_name:
            url += f"&accountName={quote(account_name)}"

        return url

    def get_bank_code(self, bank_name: str) -> str:
        """
        Get bank code from bank name

        Common Vietnamese banks
        """
        bank_codes = {
            "vietcombank": "970436",
            "vcb": "970436",
            "techcombank": "970407",
            "tcb": "970407",
            "mbbank": "970422",
            "mb": "970422",
            "acb": "970416",
            "vietinbank": "970415",
            "vpbank": "970432",
            "tpbank": "970423",
            "sacombank": "970403",
            "bidv": "970418",
            "agribank": "970405",
            "hdbank": "970437",
            "shb": "970443",
            "vib": "970441",
            "msb": "970426",
            "ocb": "970448",
            "seabank": "970440",
            "lienvietpostbank": "970449",
            "pvcombank": "970412",
            "baovietbank": "970438",
            "gpbank": "970408",
            "dongabank": "970406",
            "vietabank": "970427",
            "bacabank": "970409",
            "kienlongbank": "970452",
            "abbank": "970425",
            "namabank": "970428",
            "pgbank": "970430",
            "vietbank": "970433",
            "ncb": "970419",
            "oceanbank": "970414",
            "cbbank": "970444",
            "wooribank": "970457",
            "shinhanbank": "970424",
            "publicbank": "970439",
            "hongleongbank": "970442",
            "indovinabank": "970434",
            "standardchartered": "970410",
            "cimb": "970454",
        }

        # Normalize bank name
        normalized = bank_name.lower().strip().replace(" ", "")

        return bank_codes.get(normalized, "970436")  # Default to Vietcombank


# Singleton instance
vietqr_service = VietQRService()
