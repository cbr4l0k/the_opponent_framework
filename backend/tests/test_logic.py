#!/usr/bin/env python3
"""
Simple test script to demonstrate the 3-agent workflow:
1. Create a note using NoMa method
2. Link it to related notes
3. Challenge the arguments with opposition

This is a minimal example for learning purposes.
"""

import asyncio
from pathlib import Path

# Import RAG components
from src.opponent.rag.vectorstore import VectorStore
from src.opponent.rag.retrieval import Retriever

# Import agents
from src.opponent.agents.noma_note_creator import NomaNoteCreator
from src.opponent.agents.note_linker import NoteLinker
from src.opponent.agents.opponent_agent import OpponentAgent

async def main():
    """Run the complete workflow: Create → Link → Challenge"""

    print("=" * 60)
    print("THE OPPONENT FRAMEWORK - Mini Demo")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # STEP 0: Configuration
    # -------------------------------------------------------------------------
    print("\n[STEP 0] Configuration")

    OLLAMA_MODEL = "phi3:3.8b"  # Change to your installed model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Sentence transformer model
    VAULT_PATH = "./test_vault"  # Test vault directory
    CHROMA_PATH = "./test_chroma"  # ChromaDB storage

    # Create test vault if it doesn't exist
    vault_dir = Path(VAULT_PATH)
    vault_dir.mkdir(exist_ok=True)

    # Create a sample note in the vault for testing linking/opposition
    sample_note = vault_dir / "sample_existing_note.md"
    if not sample_note.exists():
        sample_note.write_text("""---
title: The Benefits of Remote Work
tags:
    - #s/noma
    - #c/selfstudy
    - #t/work
---

Remote work has revolutionized how we approach productivity. Studies show that workers are more productive at home without office distractions. Companies save money on office space and employees save time on commuting.

However, some research suggests that prolonged isolation can lead to decreased collaboration and innovation. Face-to-face interactions often spark creative breakthroughs that video calls cannot replicate.
""")
        print(f"✓ Created sample note: {sample_note}")

    # -------------------------------------------------------------------------
    # STEP 1: Initialize RAG Components
    # -------------------------------------------------------------------------
    print("\n[STEP 1] Initializing RAG Components...")

    vectorstore = VectorStore(
        persist_directory=CHROMA_PATH,
        collection_name="test_notes",
        embedding_model_name=EMBEDDING_MODEL
    )
    print("✓ VectorStore initialized")

    # Index the vault
    stats = vectorstore.index_vault(VAULT_PATH)
    print(f"✓ Indexed vault: {stats['total_notes']} notes, {stats['total_chunks']} chunks")

    retriever = Retriever(
        vectorstore=vectorstore,
        ollama_model=OLLAMA_MODEL,
        top_k=3
    )
    print("✓ Retriever initialized")

    # -------------------------------------------------------------------------
    # STEP 2: Create a Note (NoMa Method)
    # -------------------------------------------------------------------------
    print("\n[STEP 2] Creating a Note using NoMa Method...")

    noma_creator = NomaNoteCreator(ollama_model=OLLAMA_MODEL)
    print("✓ NoMaNoteCreator initialized")

    # Sample NoMa responses (normally from user input)
    noma_input = {
        "interesting": "I find it fascinating how AI is changing the workplace, especially with remote work becoming more common.",
        "reminds_me": "This reminds me of the industrial revolution, where technology fundamentally changed how and where people worked.",
        "similar_because": "It's similar to past technological shifts because it's creating both opportunities and anxieties about job displacement.",
        "different_because": "It's different because the pace of change is much faster, and the impact is more global and immediate.",
        "important_because": "It's important because we need to understand how to adapt our skills and work culture to this new paradigm.",
        "has_internet": False  # Set to True if you want resource fetching
    }

    print("\nRunning NoMa workflow...")
    result = await noma_creator.app.ainvoke(noma_input)

    print("\n" + "─" * 60)
    print("CREATED NOTE:")
    print("─" * 60)
    print(f"Title: {result['note_title']}")
    print(f"Tags: {', '.join(result['topic_tags'] or [])}")
    print(f"\nContent:\n{result['synthesized_note'][:300]}...")
    print("─" * 60)

    # Save the note
    note_filename = result['output_file_name']
    note_path = vault_dir / note_filename
    note_path.write_text(result['final_output'])
    print(f"✓ Saved note to: {note_path}")

    # Re-index to include the new note
    vectorstore.index_vault(VAULT_PATH)

    # -------------------------------------------------------------------------
    # STEP 3: Link Related Notes
    # -------------------------------------------------------------------------
    print("\n[STEP 3] Finding Related Notes...")

    note_linker = NoteLinker(
        retriever=retriever,
        max_links=3
    )
    print("✓ NoteLinker initialized")

    link_result = await note_linker.run(
        note_path=str(note_path),
        note_content=result['synthesized_note']
    )

    print("\n" + "─" * 60)
    print("SUGGESTED LINKS:")
    print("─" * 60)
    print(link_result['link_summary'])
    print("─" * 60)

    # -------------------------------------------------------------------------
    # STEP 4: Challenge the Arguments (Opponent)
    # -------------------------------------------------------------------------
    print("\n[STEP 4] Challenging the Arguments...")

    opponent = OpponentAgent(
        retriever=retriever,
        ollama_model=OLLAMA_MODEL,
        max_evidence=3
    )
    print("✓ OpponentAgent initialized")

    opposition_result = await opponent.run(
        note_content=result['synthesized_note'],
        note_path=str(note_path),
        context="This note discusses AI and remote work transformation"
    )

    print("\n" + "─" * 60)
    print("OPPONENT ANALYSIS:")
    print("─" * 60)
    print(f"Summary:\n{opposition_result['summary']}\n")
    print(f"Detailed Analysis:\n{opposition_result['detailed_analysis'][:500]}...")
    print("\n─" * 60)
    print(f"Counter-evidence sources: {len(opposition_result['counter_evidence'] or [])}")
    print("─" * 60)

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE!")
    print("=" * 60)
    print(f"""
Summary:
1. ✓ Created note: "{result['note_title']}"
2. ✓ Found {len(link_result['suggested_links'] or [])} related notes
3. ✓ Generated opposition using {len(opposition_result['counter_evidence'] or [])} sources

Check the {VAULT_PATH} directory for the generated note!
""")


if __name__ == "__main__":
    print("\nStarting The Opponent Framework demo...")
    print("Make sure Ollama is running with your model!\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Is Ollama running? Try: ollama list")
        print("2. Is the model installed? Try: ollama pull llama3.1")
        print("3. Check that all dependencies are installed")
        raise
