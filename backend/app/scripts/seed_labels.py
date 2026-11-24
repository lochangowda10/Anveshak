"""Entry point for the VASP label seeder introduced with attribution models."""


async def main() -> None:
    """Keep startup idempotent before the Milestone 4 label schema is installed."""
    return None


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
