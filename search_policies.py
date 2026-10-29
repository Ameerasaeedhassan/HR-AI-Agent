from pathlib import Path
from collections import Counter
import json
import re

import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "processed"

# Remove common question words that add little search value.
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by",
    "can", "democo", "do", "does", "for", "from", "how",
    "i", "in", "is", "it", "many", "me", "my", "of",
    "on", "or", "the", "to", "what", "when", "where",
    "which", "who", "with",
}


def tokenize(text):
    return [
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if word not in STOP_WORDS
    ]


class PolicyRetriever:
    def __init__(self):
        self.chunks = json.loads(
            (DATA_DIR / "policy_chunks.json").read_text(
                encoding="utf-8"
            )
        )
        manifest = json.loads(
            (DATA_DIR / "embedding_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.embeddings = np.load(
            DATA_DIR / "policy_embeddings.npy",
            allow_pickle=False,
        )

        chunk_ids = [chunk["id"] for chunk in self.chunks]

        if not self.chunks:
            raise ValueError("No policy chunks were found.")

        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("Policy chunk IDs must be unique.")

        if chunk_ids != manifest["chunk_ids"]:
            raise ValueError(
                "Chunks changed. Run build_embeddings.py again."
            )

        expected_shape = (
            len(self.chunks),
            manifest["dimensions"],
        )
        if self.embeddings.shape != expected_shape:
            raise ValueError(
                "Embedding shape does not match the manifest."
            )

        if not manifest["normalize_embeddings"]:
            raise ValueError(
                "This search requires normalized embeddings."
            )

        self.model = SentenceTransformer(
            manifest["model_name"],
            device="cpu",
        )

        # Build a small keyword index from the existing chunks.
        self.document_terms = [
            Counter(tokenize(chunk["text"]))
            for chunk in self.chunks
        ]

        self.document_lengths = np.array(
            [
                sum(terms.values())
                for terms in self.document_terms
            ],
            dtype=float,
        )
        self.average_length = max(
            float(self.document_lengths.mean()),
            1.0,
        )

        document_frequency = Counter()
        for terms in self.document_terms:
            document_frequency.update(terms.keys())

        count = len(self.chunks)

        # Words found in fewer chunks receive greater weight.
        self.idf = {
            term: float(
                np.log(
                    1 + (count - frequency + 0.5)
                    / (frequency + 0.5)
                )
            )
            for term, frequency in document_frequency.items()
        }

    def keyword_scores(self, question):
        """BM25 keyword scoring with document-length adjustment."""
        scores = np.zeros(len(self.chunks), dtype=float)
        query_terms = set(tokenize(question))

        k1 = 1.5
        b = 0.75

        for index, terms in enumerate(self.document_terms):
            length_adjustment = k1 * (
                1 - b
                + b * self.document_lengths[index]
                / self.average_length
            )

            for term in query_terms:
                frequency = terms.get(term, 0)

                if frequency:
                    scores[index] += (
                        self.idf[term]
                        * frequency
                        * (k1 + 1)
                        / (frequency + length_adjustment)
                    )

        return scores

    def search(self, question, top_k=3):
        if not question.strip():
            raise ValueError("Please enter a question.")

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        query_vector = self.model.encode(
            question,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        semantic_scores = self.embeddings @ query_vector
        lexical_scores = self.keyword_scores(question)

        # Combine rankings, because BM25 and cosine scores
        # use different numerical scales.
        # This is weighted reciprocal rank fusion.
        combined_scores = np.zeros(len(self.chunks), dtype=float)
        rank_constant = 60

        semantic_order = np.argsort(
            -semantic_scores,
            kind="stable",
        )
        for rank, index in enumerate(semantic_order, start=1):
            combined_scores[index] += 1.0 / (
                rank_constant + rank
            )

        lexical_order = np.argsort(
            -lexical_scores,
            kind="stable",
        )
        # Give keyword ranking extra influence.
        # Zero-match chunks receive no keyword contribution.
        matching_indices = [
            index
            for index in lexical_order
            if lexical_scores[index] > 0
        ]
        for rank, index in enumerate(matching_indices, start=1):
            combined_scores[index] += 2.0 / (
                rank_constant + rank
            )

        best_indices = np.argsort(
            -combined_scores,
            kind="stable",
        )[:top_k]

        # Keep "score" and "chunk" for policy_qa.py compatibility.
        return [
            {
                "score": float(combined_scores[index]),
                "semantic_score": float(semantic_scores[index]),
                "keyword_score": float(lexical_scores[index]),
                "chunk": self.chunks[int(index)],
            }
            for index in best_indices
        ]


def main():
    retriever = PolicyRetriever()

    try:
        while True:
            question = input(
                "\nAsk an HR question (or type exit): "
            ).strip()

            if question.lower() == "exit":
                break

            if not question:
                continue

            for rank, result in enumerate(
                retriever.search(question),
                start=1,
            ):
                chunk = result["chunk"]

                print(
                    f"\n{rank}. [{chunk['id']}] "
                    f"{chunk['metadata']['section_title']}"
                )
                print(f"Hybrid score: {result['score']:.4f}")
                print(
                    f"Semantic similarity: "
                    f"{result['semantic_score']:.3f}"
                )
                print(
                    f"Keyword score: "
                    f"{result['keyword_score']:.3f}"
                )
                print(f"Source: {chunk['metadata']['source']}")
                print(chunk["text"])

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()