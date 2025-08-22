from sqlalchemy import select

from app.db.models.system_setting import SystemSetting
from app.db.session import async_session_maker


class SettingNotFoundError(KeyError):
    """Raised when a requested system setting does not exist."""


async def has_setting(setting_name: str) -> bool:
    """Return True if a system setting with the given name exists, else False."""
    async with async_session_maker() as db:
        stmt = select(SystemSetting.id).where(SystemSetting.name == setting_name).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None


async def get_setting(setting_name: str) -> str:
    """
    Look up a system setting by name and return its value.

    Raises SettingNotFoundError if the setting does not exist.
    """
    async with async_session_maker() as db:
        stmt = select(SystemSetting).where(SystemSetting.name == setting_name)
        result = await db.execute(stmt)
        setting = result.scalars().first()
        if not setting:
            raise SettingNotFoundError(f"System setting not found: {setting_name}")
        return setting.value


async def get_setting_int(setting_name: str) -> int:
    """
    Retrieve a system setting by name and return it as an integer.

    Uses get_setting to obtain the string value, then converts it to int.
    Raises ValueError if the value is not a properly formatted integer.
    """
    value = await get_setting(setting_name)
    try:
        return int(value.strip())
    except Exception:
        raise ValueError(f"System setting '{setting_name}' has non-integer value: {value!r}")


async def set_setting(setting_name: str, value: str) -> str:
    """
    Create or update a system setting with the given name and value.

    If the record exists, it is updated. Otherwise, it is created.
    Returns the stored value.
    """
    async with async_session_maker() as db:
        stmt = select(SystemSetting).where(SystemSetting.name == setting_name)
        result = await db.execute(stmt)
        setting = result.scalars().first()

        if setting:
            setting.value = value
        else:
            setting = SystemSetting(name=setting_name, value=value)
            db.add(setting)

        await db.commit()
        # No need to refresh since we only return the value
        return value


__all__ = ["get_setting", "get_setting_int", "set_setting", "has_setting", "SettingNotFoundError"]
