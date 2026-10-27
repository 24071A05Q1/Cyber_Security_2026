from src.retrieval.local import get_local_retriever


def test_network_runbook_is_retrieved():
    docs = get_local_retriever().retrieve("Device receives a 169.254 address", category="network", top_k=3)
    assert any(doc.source_id.startswith("RB-NET") for doc in docs)
