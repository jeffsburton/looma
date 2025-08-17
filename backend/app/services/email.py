from typing import Iterable, Optional, Union
import smtplib
from email.message import EmailMessage
from app.core.config import settings
from threading import Lock
import sys

Address = Union[str, tuple[str, str]]  # "email" or ("Name", "email")

# In-memory outbox for tests when using the "memory" backend
_outbox: list[EmailMessage] = []
_outbox_lock = Lock()


def get_outbox() -> list[EmailMessage]:
    with _outbox_lock:
        return list(_outbox)


def clear_outbox() -> None:
    with _outbox_lock:
        _outbox.clear()


def _format_address(addr: Address) -> str:
    if isinstance(addr, tuple):
        name, email = addr
        return f"{name} <{email}>"
    return addr


def send_email(
    to: Union[Address, Iterable[Address]],
    subject: str,
    text: Optional[str] = None,
    html: Optional[str] = None,
    sender: Optional[Address] = None,
    cc: Optional[Iterable[Address]] = None,
    bcc: Optional[Iterable[Address]] = None,
    reply_to: Optional[Address] = None,
) -> None:
    """
    Send an email. Backend is chosen by settings.email_backend:
      - "smtp" (default): real SMTP delivery
      - "console": write the email to stdout
      - "memory": store the email in an in-memory outbox for tests

    Supports plain text and HTML.
    """
    if not text and not html:
        raise ValueError("Either text or html content must be provided")

    backend = getattr(settings, "email_backend", "smtp").lower().strip()

    # Determine sender
    from_addr = _format_address(sender) if sender else (settings.smtp_from or settings.smtp_username or "")
    if not from_addr:
        raise RuntimeError("SMTP sender is not configured. Set smtp_from or smtp_username in settings.")

    # Normalize recipients to list of strings
    def normalize(addrs: Optional[Union[Address, Iterable[Address]]]) -> list[str]:
        if addrs is None:
            return []
        if isinstance(addrs, (str, tuple)):
            return [_format_address(addrs)]
        return [_format_address(a) for a in addrs]

    to_addrs = normalize(to)
    cc_addrs = normalize(cc)
    bcc_addrs = normalize(bcc)

    if not to_addrs and not cc_addrs and not bcc_addrs:
        raise ValueError("At least one recipient (to/cc/bcc) must be provided")

    # Build the message
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    if to_addrs:
        msg["To"] = ", ".join(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
    if reply_to:
        msg["Reply-To"] = _format_address(reply_to)

    if text and html:
        msg.set_content(text)
        msg.add_alternative(html, subtype="html")
    elif html:
        # Provide a minimal plain-text fallback
        msg.set_content("This message contains HTML content. Please use an HTML-capable email client.")
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(text or "")

    all_recipients = to_addrs + cc_addrs + bcc_addrs

    if backend == "memory":
        with _outbox_lock:
            _outbox.append(msg)
        return

    if backend == "console":
        out = sys.stdout
        print("=== EMAIL (console backend) ===", file=out)
        print(f"From: {from_addr}", file=out)
        if to_addrs:
            print(f"To: {', '.join(to_addrs)}", file=out)
        if cc_addrs:
            print(f"Cc: {', '.join(cc_addrs)}", file=out)
        if bcc_addrs:
            print(f"Bcc: {', '.join(bcc_addrs)}", file=out)
        print(f"Subject: {subject}", file=out)
        print("\n-- Body (text) --", file=out)
        if text:
            print(text, file=out)
        if html:
            print("\n-- Body (html) --", file=out)
            print(html, file=out)
        print("=== END EMAIL ===", file=out)
        return

    # Default: SMTP backend
    host = settings.smtp_host
    port = settings.smtp_port
    username = settings.smtp_username
    password = settings.smtp_password

    if not host or not port:
        raise RuntimeError("SMTP host/port not configured")

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        if settings.smtp_use_tls:
            server.starttls()
            server.ehlo()
        if username and password:
            server.login(username, password)
        server.send_message(msg, from_addr=from_addr, to_addrs=all_recipients)


__all__ = ["send_email", "get_outbox", "clear_outbox"]
