"""Quick smoke test for the RepoMinds pipeline components."""

print("=" * 50)
print("RepoMinds — Component Tests")
print("=" * 50)

# 1. Test chunker
print("\n[1/4] Testing chunker...")
from src.chunker import chunk_code

code = """def hello():
    print("hello world")

def goodbye():
    print("goodbye world")

class Foo:
    def bar(self):
        return 42

    def baz(self):
        for i in range(100):
            print(i)
"""

chunks = chunk_code("test.py", code)
assert len(chunks) > 0, "Chunker returned no chunks"
print(f"  ✅ chunk_code produced {len(chunks)} chunk(s)")
for i, c in enumerate(chunks):
    print(f"     chunk {i+1}: lines {c['start_line']}-{c['end_line']}, chars={len(c['text'])}")

# 2. Test embedder
print("\n[2/4] Testing embedder...")
from src.embedder import embed_chunks, embed_query

q_vec = embed_query("What does the hello function do?")
assert q_vec.shape[0] == 1, f"Expected 1 row, got {q_vec.shape[0]}"
assert q_vec.shape[1] == 384, f"Expected dim 384, got {q_vec.shape[1]}"
print(f"  ✅ embed_query shape: {q_vec.shape}")

c_vecs = embed_chunks(chunks)
assert c_vecs.shape[0] == len(chunks)
print(f"  ✅ embed_chunks shape: {c_vecs.shape}")

# 3. Test FAISS vector store
print("\n[3/4] Testing vector store...")
from src.vector_store import build_index, search

index = build_index(c_vecs)
results = search(index, q_vec, chunks, k=1)
assert len(results) > 0, "Search returned no results"
print(f"  ✅ search returned {len(results)} result(s)")
print(f"     top result: {results[0]['file_path']} L{results[0]['start_line']}-{results[0]['end_line']} (score: {results[0]['score']:.4f})")

# 4. Test repo_loader (dry)
print("\n[4/4] Testing repo_loader imports...")
from src.repo_loader import clone_repo, extract_code_files
print("  ✅ repo_loader imports OK")

print("\n" + "=" * 50)
print("All component tests passed! ✅")
print("=" * 50)
