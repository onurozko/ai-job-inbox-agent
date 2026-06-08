"""Seed local demo data for portfolio presentations."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.db.session import close_db, get_session_factory, init_db
from app.demo.guard import DemoScriptsNotAllowedError, ensure_demo_scripts_allowed
from app.demo.seed import seed_demo_data


async def run_seed() -> int:
    ensure_demo_scripts_allowed(get_settings())
    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as session:
        result = await seed_demo_data(session)
        await session.commit()

    await close_db()

    print("Demo data seeded successfully.")
    print(f"  user_id: {result.user_id}")
    print(f"  user_created: {result.user_created}")
    print(f"  profile_created: {result.profile_created}")
    print(f"  emails_created: {result.emails_created}")
    print(f"  emails_skipped: {result.emails_skipped}")
    print(f"  applications_count: {result.applications_count}")
    print(f"  events_count: {result.events_count}")
    print("\nNext step: python scripts/create_demo_token.py")
    return 0


def main() -> None:
    try:
        raise SystemExit(asyncio.run(run_seed()))
    except DemoScriptsNotAllowedError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
