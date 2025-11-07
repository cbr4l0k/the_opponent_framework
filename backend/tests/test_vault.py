#!/usr/bin/env python3
"""Debug script to test vault indexing."""

import asyncio
import httpx
from pathlib import Path


async def test_vault_endpoint():
    """Test if the vault indexing endpoint works."""
    print("\n" + "=" * 60)
    print("Testing Vault Indexing Endpoint")
    print("=" * 60)

    test_vault = Path("./test_vault").absolute()

    print(f"\nTest vault path: {test_vault}")
    print(f"Vault exists: {test_vault.exists()}")

    if test_vault.exists():
        notes = list(test_vault.glob("*.md"))
        print(f"Notes in vault: {len(notes)}")
        for note in notes:
            print(f"  - {note.name}")

    print("\n" + "-" * 60)
    print("Attempting to index vault...")
    print("-" * 60)

    try:
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120.0) as client:
            # Test vault health
            print("\n1. Testing vault health endpoint...")
            response = await client.get("/api/vault/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")

            # Index vault
            print("\n2. Indexing vault...")
            request_data = {"vault_path": str(test_vault)}
            response = await client.post("/api/vault/index", json=request_data)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print( "   ✓ Success!")
                print(f"   ✓ Indexed notes: {result['total_notes']}")
                print(f"   ✓ Created chunks: {result['total_chunks']}")
            else:
                print(f"   ❌ Error: {response.text}")

            # Test a search to verify
            print("\n3. Testing if notes are searchable...")
            link_request = {
                "note_path": "test.md",
                "note_content": "AI workplace remote work automation",
                "max_links": 3
            }
            response = await client.post("/api/links/find", json=link_request)
            if response.status_code == 200:
                result = response.json()
                print(f"   Found {result['count']} related notes")
                if result['count'] > 0:
                    print("   ✓ Vault is properly indexed!")
                    for link in result['suggested_links']:
                        print(f"      - {link['title']}")
                else:
                    print("   ⚠️  No results found (vault might be empty or not indexed)")
            else:
                print(f"   ❌ Search failed: {response.text}")

    except httpx.ConnectError:
        print("\n❌ Cannot connect to API server!")
        print("   Make sure the server is running:")
        print("   uvicorn opponent.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_vault_endpoint())
