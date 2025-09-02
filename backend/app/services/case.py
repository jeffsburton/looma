from __future__ import annotations

from datetime import date as Date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.case import Case


async def create_case_number(db: AsyncSession, state_code: str, when: Optional[Date] = None) -> str:
    """
    Create a new case number using the pattern: YY-[STATE]-MM###

    - YY: last two digits of the year from the date
    - STATE: provided two-letter state code (normalized to upper-case)
    - MM: zero-padded month from the date
    - ###: zero-padded sequence number for that year (COUNT + 1 based on existing records
      where case_number LIKE 'YY-%')

    Args:
        db: Async SQLAlchemy session
        state_code: Two-letter state code (e.g., "CA")
        when: Optional date to use; if None, uses today's date

    Returns:
        The newly generated case number string.
    """
    if not state_code or len(state_code.strip()) != 2 or not state_code.strip().isalpha():
        raise ValueError("state_code must be a two-letter alphabetic code, e.g., 'CA'")

    when = when or Date.today()

    yy = f"{when:%y}"
    mm = f"{when:%m}"
    st = state_code.strip().upper()

    # Count existing cases for the year prefix 'YY-%'
    like_prefix = f"{yy}-%"
    stmt = select(func.count()).select_from(Case).where(Case.case_number.like(like_prefix))
    result = await db.execute(stmt)
    count_for_year: int = int(result.scalar_one() or 0)

    seq = count_for_year + 1
    case_number = f"{yy}-{st}-{mm}{seq:03d}"
    return case_number
