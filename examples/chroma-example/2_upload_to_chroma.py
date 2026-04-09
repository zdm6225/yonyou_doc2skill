#!/usr/bin/env python3
"""
Step 2: Upload to ChromaDB

This script:
1. Creates a ChromaDB client (in-memory or persistent)
2. Creates a collection
3. Adds all documents with metadata
4. Verifies the upload

Usage:
    # In-memory (development)
    python 2_upload_to_chroma.py

    # Persistent storage (production)
    python 2_upload_to_chroma.py --persist ./chroma_db

    # Reset existing collection
    python 2_upload_to_chroma.py --reset
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import chromadb
except ImportError:
    print("❌ chromadb not installed!")
    print("Install it with: pip install chromadb")
    sys.exit(1)

def create_client(persist_directory: str = None):
    """Create ChromaDB client."""
    print("\n📊 Creating ChromaDB client...")

    try:
        if persist_directory:
            # Persistent client (saves to disk)
            client = chromadb.PersistentClient(path=persist_directory)
            print(f"✅ Client created (persistent: {persist_directory})\n")
        else:
            # In-memory client (faster, but data lost on exit)
            client = chromadb.Client()
            print("✅ Client created (in-memory)\n")

        return client

    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        sys.exit(1)

def load_skill_data(filepath: str = "output/vue-chroma.json"):
    """Load the ChromaDB-format skill JSON."""
    path = Path(filepath)

    if not path.exists():
        print(f"❌ Skill file not found: {filepath}")
        print("Run '1_generate_skill.py' first!")
        sys.exit(1)

    with open(path) as f:
        return json.load(f)

def create_collection(client, collection_name: str, reset: bool = False):
    """Create ChromaDB collection."""
    print(f"📦 Creating collection: {collection_name}")

    try:
        # Check if collection exists
        existing_collections = [c.name for c in client.list_collections()]

        if collection_name in existing_collections:
            if reset:
                print(f"🗑️  Deleting existing collection...")
                client.delete_collection(collection_name)
            else:
                print(f"⚠️  Collection '{collection_name}' already exists")
                response = input("Delete and recreate? [y/N]: ")
                if response.lower() == "y":
                    client.delete_collection(collection_name)
                else:
                    print("Using existing collection")
                    return client.get_collection(collection_name)

        # Create collection
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Yonyou Doc2Skill documentation"}
        )
        print("✅ Collection created!\n")
        return collection

    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        sys.exit(1)

def upload_documents(collection, data: dict):
    """Add documents to collection."""
    total = len(data["documents"])

    print(f"📤 Adding {total} documents to collection...")

    try:
        # Add all documents in one batch
        collection.add(
            documents=data["documents"],
            metadatas=data["metadatas"],
            ids=data["ids"]
        )

        print(f"✅ Successfully added {total} documents to ChromaDB\n")

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)

def verify_upload(collection):
    """Verify documents were uploaded correctly."""
    count = collection.count()
    print(f"🔍 Collection '{collection.name}' now contains {count} documents")

def main():
    parser = argparse.ArgumentParser(description="Upload skill to ChromaDB")
    parser.add_argument(
        "--persist",
        help="Persistent storage directory (e.g., ./chroma_db)"
    )
    parser.add_argument(
        "--file",
        default="output/vue-chroma.json",
        help="Path to ChromaDB JSON file"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collection before uploading"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Step 2: Upload to ChromaDB")
    print("=" * 60)

    # Create client
    client = create_client(args.persist)

    # Load skill data
    data = load_skill_data(args.file)

    # Create collection
    collection = create_collection(client, data["collection_name"], args.reset)

    # Upload documents
    upload_documents(collection, data)

    # Verify
    verify_upload(collection)

    if args.persist:
        print(f"\n💾 Data saved to: {args.persist}")
        print("   Use --persist flag to load it next time")

    print("\n✅ Upload complete! Next step: python 3_query_example.py")

    if args.persist:
        print(f"   python 3_query_example.py --persist {args.persist}")

if __name__ == "__main__":
    main()
