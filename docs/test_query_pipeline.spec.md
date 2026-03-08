# test_query_pipeline.py

## Verifies the embedding pipeline processes multiple inputs
**What it tests:** The embedder produces different vectors for different texts
**Steps:**
1. Create 3 text strings with different content
2. Call `embed()` with each one separately
3. Compare the resulting vectors with each other
4. Verify that no pair of vectors is identical

## Handles an empty string without raising an exception
**What it tests:** The embedder does not crash when it receives empty input
**Steps:**
1. Call `embed("")`
2. Verify it returns a zero vector or raises a controlled ValueError
3. Check that the error includes a descriptive message if applicable

## Retrieves the top-k most relevant documents for a query
**What it tests:** The retriever returns exactly k documents ordered by score
**Steps:**
1. Insert 10 test documents into Weaviate
2. Run a query with k=3
3. Verify that exactly 3 results are returned
4. Verify they are ordered from highest to lowest relevance
5. Clean up the test documents at the end
