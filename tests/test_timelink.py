"""Check temporal connectivity against an independent graph-search oracle."""

import random
import unittest
from collections import deque

from timelink import solve


def replay(nodes, events):
    active = set()
    answers = []
    for index, event in enumerate(events):
        edge = frozenset((event["u"], event["v"]))
        if event["kind"] == "add":
            active.add(edge)
        elif event["kind"] == "remove":
            active.remove(edge)
        else:
            seen = {event["u"]}
            queue = deque(seen)
            while queue:
                current = queue.popleft()
                for link in active:
                    if current in link:
                        other = next(node for node in link if node != current)
                        if other not in seen:
                            seen.add(other)
                            queue.append(other)
            answers.append({"event": index, "u": event["u"], "v": event["v"],
                            "connected": event["v"] in seen})
    return answers


class TimeLinkTests(unittest.TestCase):
    def test_example_has_both_connected_and_disconnected_answers(self):
        nodes = ["api", "db", "worker"]
        events = [
            {"kind": "add", "u": "api", "v": "db"},
            {"kind": "add", "u": "db", "v": "worker"},
            {"kind": "query", "u": "api", "v": "worker"},
            {"kind": "remove", "u": "api", "v": "db"},
            {"kind": "query", "u": "api", "v": "worker"},
        ]
        self.assertEqual(solve({"nodes": nodes, "events": events}), replay(nodes, events))

    def test_generated_timelines_match_graph_search(self):
        nodes = [str(i) for i in range(6)]
        edges = [(nodes[i], nodes[j]) for i in range(6) for j in range(i + 1, 6)]
        for seed in range(80):
            rng = random.Random(seed)
            active = set()
            events = []
            for _ in range(90):
                u, v = rng.choice(edges)
                edge = (u, v)
                if rng.random() < 0.4:
                    kind = "query"
                elif edge in active:
                    kind = "remove"
                    active.remove(edge)
                else:
                    kind = "add"
                    active.add(edge)
                events.append({"kind": kind, "u": u, "v": v})
            document = {"nodes": nodes, "events": events}
            with self.subTest(seed=seed):
                self.assertEqual(solve(document), replay(nodes, events))

    def test_rejects_invalid_edge_lifecycle(self):
        nodes = ["a", "b"]
        for kinds in (["remove"], ["add", "add"], ["add", "remove", "remove"]):
            events = [{"kind": kind, "u": "a", "v": "b"} for kind in kinds]
            with self.subTest(kinds=kinds), self.assertRaises(ValueError):
                solve({"nodes": nodes, "events": events})


if __name__ == "__main__":
    unittest.main()
