"""Insert an additive synthetic fixture and check SQL/MCP/vector retrieval, no LLM."""
import json
from time import perf_counter
from src.repositories.base_repository import get_connection
from src.repositories.vector_repository import insert_embeddings, search_similar_reviews
from src.embeddings.embedding_client import get_embedding_client
from src.mcp.client import call_tool_via_mcp

FIXTURE = [
    ("DEMO-SYNTHETIC: Practical Python", 5, "Clear Python lessons", "The Python programming examples explain functions and data analysis clearly."),
    ("DEMO-SYNTHETIC: Practical Python", 4, "Helpful exercises", "Useful Python coding exercises for beginners learning programming."),
    ("DEMO-SYNTHETIC: Garden Handbook", 3, "Good planting advice", "The garden book explains watering plants and growing vegetables."),
    ("DEMO-SYNTHETIC: Garden Handbook", 2, "Missing soil guidance", "The gardening advice lacks details about soil and plant diseases."),
    ("DEMO-SYNTHETIC: Slow Mystery", 1, "Slow plot", "The mystery novel has a slow plot and repetitive detective scenes."),
    ("DEMO-SYNTHETIC: Slow Mystery", 2, "Weak ending", "The detective story ends abruptly and the mystery is not convincing."),
]

def run():
    started = perf_counter()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM app.reviews WHERE user_id IS NULL OR user_id NOT LIKE 'demo-synthetic-v1-%%'")
            if cur.fetchone()[0] != 0:
                raise RuntimeError("Use a dedicated synthetic database; unrelated reviews found")
    client = get_embedding_client()
    vectors = client.embed_texts([row[3] for row in FIXTURE])
    records = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            for index, (title, score, summary, text) in enumerate(FIXTURE):
                cur.execute("SELECT book_pk FROM app.books WHERE title=%s ORDER BY book_pk LIMIT 1", (title,))
                found = cur.fetchone()
                if found:
                    book_pk = found[0]
                else:
                    cur.execute("INSERT INTO app.books(title, normalized_title) VALUES (%s,%s) RETURNING book_pk", (title, title.lower()))
                    book_pk = cur.fetchone()[0]
                marker = f"demo-synthetic-v1-{index}"
                cur.execute("SELECT review_pk FROM app.reviews WHERE user_id=%s AND book_pk=%s ORDER BY review_pk LIMIT 1", (marker, book_pk))
                found = cur.fetchone()
                if found:
                    review_pk = found[0]
                else:
                    cur.execute("INSERT INTO app.reviews(book_pk,title,user_id,profile_name,score,review_summary,review_text) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING review_pk", (book_pk,title,marker,"Synthetic reviewer",score,summary,text))
                    review_pk = cur.fetchone()[0]
                records.append(dict(review_pk=review_pk,book_pk=book_pk,embedding=vectors[index],model_name=client.model_name,embedding_dimension=384,pipeline_version="demo-synthetic-v1"))
        conn.commit()
        insert_embeddings(conn,records)
        # Only tune the known synthetic-only database. Never change an index
        # over unrelated reviews. A 100-list empty-built index loses recall here.
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM app.reviews WHERE user_id IS NULL OR user_id NOT LIKE 'demo-synthetic-v1-%%'")
            if cur.fetchone()[0] != 0:
                raise RuntimeError("Use a dedicated synthetic database; unrelated reviews found")
            cur.execute("DROP INDEX IF EXISTS app.idx_review_embeddings_vector")
            cur.execute("CREATE INDEX idx_review_embeddings_vector ON app.review_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists=1)")
        conn.commit()
        # The existing IVFFlat index was created with an empty database. For
        # this tiny fixture force exact scan in this session, without dropping it.
        with conn.cursor() as cur:
            cur.execute("SET enable_indexscan = off")
            cur.execute("SET enable_bitmapscan = off")
        rows = search_similar_reviews(conn,"Python programming functions and coding examples",top_k=2)
        assert len(rows) == 2, rows
        assert all(row["title"] == FIXTURE[0][0] for row in rows), rows
    ranked, error = call_tool_via_mcp("get_best_rated_books", {"min_reviews":1,"limit":3})
    assert error is None and ranked, (ranked,error)
    assert ranked[0]["title"] == FIXTURE[0][0], ranked
    semantic, error = call_tool_via_mcp("search_similar_reviews", {"query_text":"Python programming functions and coding examples","top_k":2})
    # Tool parameter name is validated against the actual MCP server schema.
    assert error is None and semantic, (semantic,error)
    assert len(semantic) == 2 and all(row["title"] == FIXTURE[0][0] for row in semantic), semantic
    print(json.dumps({"fixture":"demo-synthetic-v1","reviews":len(FIXTURE),"structured":ranked,"semantic_direct":rows,"semantic_mcp":semantic,"elapsed_seconds":round(perf_counter()-started,3),"bedrock_called":False},ensure_ascii=False,default=str))

if __name__ == "__main__":
    run()
