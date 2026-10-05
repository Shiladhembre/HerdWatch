from typing import Protocol


class NotificationProvider(Protocol):
    async def send_sms(self, recipient: str, message: str) -> dict: ...
    async def send_push(self, recipient: str, message: str) -> dict: ...
    async def send_email(self, recipient: str, message: str) -> dict: ...
    async def send_whatsapp(self, recipient: str, message: str) -> dict: ...
    async def send_ivr(self, recipient: str, message: str) -> dict: ...


class UnconfiguredProvider:
    async def send_sms(self, recipient, message):
        return {"delivered": False, "status": "provider_not_configured"}

    send_push = send_sms
    send_email = send_sms
    send_whatsapp = send_sms
    send_ivr = send_sms


provider = UnconfiguredProvider()
