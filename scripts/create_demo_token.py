"""Create a JWT for the local demo user."""

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
from app.demo.token import DemoUserNotFoundError, create_demo_user_token


async def run_create_token() -> int:
    ensure_demo_scripts_allowed(get_settings())
    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as session:
        token = await create_demo_user_token(session)

    await close_db()

    print(token)
    print(f"\nAuthorization: Bearer {token}")
    return 0


def main() -> None:
    try:
        raise SystemExit(asyncio.run(run_create_token()))
    except DemoScriptsNotAllowedError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except DemoUserNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
