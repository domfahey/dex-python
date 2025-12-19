"""Example usage of the Dex API client."""

from src.dex_import import DexClient


def main() -> None:
    """Fetch and display contacts from Dex."""
    with DexClient() as client:
        print("Fetching contacts from Dex...")
        contacts = client.get_contacts(limit=10)
        print(f"Found {len(contacts)} contacts")
        for contact in contacts:
            print(f"  - {contact}")


if __name__ == "__main__":
    main()
