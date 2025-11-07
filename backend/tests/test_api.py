"""Simple script to test all Opponent Framework API endpoints."""

import asyncio
import httpx
from pathlib import Path

# Timeout configuration for AI operations (in seconds)
TIMEOUT = httpx.Timeout(
    connect=10.0*9,	# Connection timeout
    read=60.0*9,	# Read timeout (increased for AI operations)
    write=10.0*9,	# Write timeout
    pool=10.0*9,	# Pool timeout
)



TEST_VAULT = Path("./test_vault")


def create_sample_notes():
    """Create sample notes in the test vault for testing."""
    print("\n" + "=" * 60)
    print("0. Setting up test vault with sample notes")
    print("=" * 60)

    TEST_VAULT.mkdir(exist_ok=True)

    # Sample note 1: Pro-remote work
    note1 = TEST_VAULT / "benefits_of_remote_work.md"
    note1.write_text("""---
title: The Benefits of Remote Work
tags:
  - #s/noma
  - #c/selfstudy
  - #t/remote-work
---

Remote work has revolutionized productivity. Studies show workers are more productive
at home without office distractions. Companies save money on office space and
employees save time on commuting.

The flexibility allows for better work-life balance, and technology enables
seamless collaboration across time zones.
""")
    print(f"✅ Created: {note1.name}")

    # Sample note 2: Concerns about AI (counter-evidence)
    note2 = TEST_VAULT / "ai_job_displacement_concerns.md"
    note2.write_text("""---
title: AI and Job Displacement Concerns
tags:
  - #s/noma
  - #c/selfstudy
  - #t/ai-risks
  - #opponent
---

Research from MIT shows that AI automation is displacing workers faster than
new jobs are being created. A 2023 study found that 40% of tasks in knowledge
work could be automated within 5 years.

The transition period is creating economic hardship for workers who lack
retraining opportunities. Historical technological shifts took decades,
but AI is advancing in years, leaving little time for adaptation.
""")
    print(f"✅ Created: {note2.name}")

    # Sample note 3: Related to workplace transformation
    note3 = TEST_VAULT / "future_of_work.md"
    note3.write_text("""---
title: The Future of Work is Hybrid
tags:
  - #s/noma
  - #c/selfstudy
  - #t/workplace
---

The post-pandemic workplace is neither fully remote nor fully in-office.
Hybrid models combine the best of both worlds: flexibility of remote work
with occasional in-person collaboration.

This approach addresses both productivity concerns and social needs of workers.
""")
    print(f"✅ Created: {note3.name}")

    print(f"\n✅ Test vault created at: {TEST_VAULT.absolute()}")
    print(f"✅ Sample notes: {len(list(TEST_VAULT.glob('*.md')))}")


async def index_test_vault():
    """Index the test vault into the vectorstore."""
    print("\n" + "=" * 60)
    print("0.5. Indexing test vault")
    print("=" * 60)

    request_data = {
        "vault_path": str(TEST_VAULT.absolute())
    }

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=TIMEOUT) as client:
        response = await client.post("/api/vault/index", json=request_data)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Indexed {result['total_notes']} notes")
            print(f"✅ Created {result['total_chunks']} chunks")
            print(f"✅ Vault path: {result['vault_path']}")
            return True
        else:
            print(f"\n❌ Error: {response.text}")
            return False


NOTE_CONTENT = """
AI is fundamentally transforming the workplace. Remote work has become
the norm, and AI tools are automating many routine tasks. This shift is
creating both opportunities and challenges for workers.

Some argue this will lead to mass unemployment, while others believe it
will create new types of jobs we haven't imagined yet.
"""

async def test_health():
    """Test all health endpoints."""
    print("\n" + "=" * 60)
    print("1. Testing Health Endpoints")
    print("=" * 60)

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Global health
        response = await client.get("/health")
        print(f"\n✅ Global Health: {response.status_code}")
        print(response.json())

        # Notes health
        response = await client.get("/api/notes/health")
        print(f"\n✅ Notes Health: {response.status_code}")
        print(response.json())

        # Links health
        response = await client.get("/api/links/health")
        print(f"\n✅ Links Health: {response.status_code}")
        print(response.json())

        # Opponent health
        response = await client.get("/api/opponent/health")
        print(f"\n✅ Opponent Health: {response.status_code}")
        print(response.json())


async def test_create_note():
    """Test creating a note using the NoMa method."""
    print("\n" + "=" * 60)
    print("2. Testing Note Creation")
    print("=" * 60)

    # Sample NoMa reflections
    request_data = {
        "interesting": "I find it fascinating how AI is changing the workplace, especially with remote work becoming more common.",
        "reminds_me": "This reminds me of the industrial revolution, where technology fundamentally changed how and where people worked.",
        "similar_because": "It's similar to past technological shifts because it's creating both opportunities and anxieties about job displacement.",
        "different_because": "It's different because the pace of change is much faster, and the impact is more global and immediate.",
        "important_because": "It's important because we need to understand how to adapt our skills and work culture to this new paradigm.",
        "has_internet": False
    }

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=TIMEOUT) as client:
        response = await client.post("/api/notes/create", json=request_data)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Title: {result['title']}")
            print(f"✅ Tags: {', '.join(result['tags'])}")
            print(f"✅ Filename: {result['filename']}")
            print("\n✅ Content Preview:")
            print(result['content'][:200] + "...")
            return result
        else:
            print(f"\n❌ Error: {response.text}")
            return None


async def test_find_links():
    """Test finding links for a note."""
    print("\n" + "=" * 60)
    print("3. Testing Note Linking")
    print("=" * 60)

    request_data = {
        "note_path": "test/ai_workplace.md",
        "note_content": NOTE_CONTENT,
        "max_links": 3
    }

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=TIMEOUT) as client:
        response = await client.post("/api/links/find", json=request_data)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Found {result['count']} related note(s)")

            if result['count'] == 0:
                print("\n⚠️  No links found. This means:")
                print("   - The vault might not be indexed yet")
                print("   - Try restarting the server with VAULT_PATH=./test_vault")
                print("   - Or the test vault has no related content")
            else:
                print(f"\n✅ Summary:\n{result['summary']}")

                if result['suggested_links']:
                    print("\n✅ Suggested Links:")
                    for i, link in enumerate(result['suggested_links'], 1):
                        print(f"   {i}. {link['title']} (score: {link['score']:.3f})")
                        print(f"      Path: {link['path']}")
            return result
        else:
            print(f"\n❌ Error: {response.text}")
            return None


async def test_challenge_claim():
    """Test challenging a claim with the opponent."""
    print("\n" + "=" * 60)
    print("4. Testing Opponent Challenge")
    print("=" * 60)

    request_data = {
        "note_content": NOTE_CONTENT,
        "context": "Discussion about AI and the future of work",
        "max_evidence": 3
    }

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=TIMEOUT) as client:
        response = await client.post("/api/opponent/challenge", json=request_data)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Evidence Count: {result['evidence_count']}")

            if result['evidence_count'] == 0:
                print("\n⚠️  No counter-evidence found. This means:")
                print("   - The vault might not be indexed yet")
                print("   - Try restarting the server with VAULT_PATH=./test_vault")
                print("   - Or add notes tagged with #opponent to your vault")
            else:
                print(f"\n✅ Summary:\n{result['summary']}")
                print("\n✅ Detailed Analysis (preview):")
                print(result['detailed_analysis'][:300] + "...")

                if result['counter_evidence']:
                    print("\n✅ Counter-evidence sources:")
                    for i, evidence in enumerate(result['counter_evidence'], 1):
                        print(f"   {i}. {evidence['source']} (score: {evidence['score']:.3f})")
                        print(f"      {evidence['content'][:100]}...")
            return result
        else:
            print(f"\n❌ Error: {response.text}")
            return None


async def main():
    """Run all tests."""
    print("\n" + "🧪" * 30)
    print("Testing Opponent Framework API")
    print("🧪" * 30)
    print("\nMake sure the API is running:")
    print("  cd backend && uv run opponent\n")

    try:
        # Setup test data
        create_sample_notes()

        # Index the test vault
        indexed = await index_test_vault()

        if not indexed:
            print("\n⚠️  Failed to index vault. Skipping linking/opponent tests")
            await test_health()
            await test_create_note()
        else:
            # Run all tests in sequence
            await test_health()
            await test_create_note()
            await test_find_links()
            await test_challenge_claim()

        print("\n" + "=" * 60)
        print("✅ Tests completed!")
        print("=" * 60)

    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to API")
        print("Start the server with: cd backend && uvicorn opponent.main:app --reload")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
