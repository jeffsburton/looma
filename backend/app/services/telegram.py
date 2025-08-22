from app.services.system_settings import get_setting, set_setting, get_setting_int


from telethon import TelegramClient
from telethon.errors import FloodWaitError

async def get_client() -> TelegramClient:
    """
    Creates a TelegramClient using a StringSession loaded from DB.
    If not present, raises so you can provision the session out-of-band.
    """
    session_str = await get_setting("system_telegram_session")
    if not session_str:
        raise RuntimeError(
            "No session found. Run the provisioning script once to create a StringSession "
            "and store it in your DB."
        )
    # Build client with the stored session
    api_id: int = await get_setting_int("system_telegram_api_id")
    api_hash: str = await get_setting("system_telegram_api_hash")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    # After connecting, Telethon may refresh the session; re-save if it changed.
    new_session_str = client.session.save()
    if new_session_str != session_str:
        await set_setting("system_telegram_session", new_session_str)
    return client

async def send_telegram_dm(to: str, text: str) -> None:
    client = await get_client()
    try:
        await client.send_message(to, text)
        # Save any session updates after activity
        await set_setting("system_telegram_session", client.session.save())
    except FloodWaitError as e:
        print(f"Rate limited. Sleep {e.seconds}s, then retry.")
    finally:
        await client.disconnect()



if __name__ == "__main__":
    # provision_session.py
    import os
    import asyncio
    import sys
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    async def main():
        await send_telegram_dm("jeffburton", "This is a test message")
        api_id: int = await get_setting_int("system_telegram_api_id")
        api_hash: str = await get_setting("system_telegram_api_hash")
        async with TelegramClient(StringSession(), api_id, api_hash) as client:
            print("Logged in. Your StringSession (store this in DB):")
            print(client.session.save())

    # Ensure Windows uses a compatible asyncio event loop for psycopg/SQLAlchemy
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    asyncio.run(main())
