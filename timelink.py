"""Offline dynamic connectivity with a segment tree and rollback DSU."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Event:
    kind: str
    u: str
    v: str


class RollbackDSU:
    def __init__(self, nodes: list[str]):
        self.parent = list(range(len(nodes)))
        self.size = [1] * len(nodes)
        self.names = {name: i for i, name in enumerate(nodes)}
        self.history: list[tuple[int, int, int]] = []

    def root(self, index: int) -> int:
        while self.parent[index] != index:
            index = self.parent[index]
        return index

    def connected(self, u: str, v: str) -> bool:
        return self.root(self.names[u]) == self.root(self.names[v])

    def union(self, u: str, v: str) -> None:
        a, b = self.root(self.names[u]), self.root(self.names[v])
        if a == b:
            return
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.history.append((b, a, self.size[a]))
        self.parent[b] = a
        self.size[a] += self.size[b]

    def snapshot(self) -> int:
        return len(self.history)

    def rollback(self, position: int) -> None:
        while len(self.history) > position:
            child, parent, old_size = self.history.pop()
            self.parent[child] = child
            self.size[parent] = old_size


def parse(document: object) -> tuple[list[str], list[Event]]:
    if not isinstance(document, dict) or set(document) != {"nodes", "events"}:
        raise ValueError("input requires exactly nodes and events")
    nodes, raw = document["nodes"], document["events"]
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 10000 or not all(
        isinstance(n, str) and 1 <= len(n) <= 80 for n in nodes
    ) or len(set(nodes)) != len(nodes):
        raise ValueError("nodes must be 1–10000 distinct nonempty strings")
    if not isinstance(raw, list) or not 1 <= len(raw) <= 50000:
        raise ValueError("events must contain 1–50000 entries")
    events = []
    known = set(nodes)
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"kind", "u", "v"}:
            raise ValueError("each event needs exactly kind, u, and v")
        kind, u, v = item["kind"], item["u"], item["v"]
        if kind not in ("add", "remove", "query") or not isinstance(u, str) or not isinstance(v, str) or u not in known or v not in known:
            raise ValueError("invalid event or unknown node")
        if kind != "query" and u == v:
            raise ValueError("self-edges are not supported")
        events.append(Event(kind, u, v))
    return nodes, events


def solve(document: object) -> list[dict]:
    nodes, events = parse(document)
    count = len(events)
    tree: list[list[tuple[str, str]]] = [[] for _ in range(4 * count)]
    active: dict[tuple[str, str], int] = {}

    def interval(index: int, left: int, right: int, start: int, end: int, edge: tuple[str, str]) -> None:
        if start <= left and right <= end:
            tree[index].append(edge)
            return
        middle = (left + right) // 2
        if start < middle:
            interval(index * 2, left, middle, start, end, edge)
        if end > middle:
            interval(index * 2 + 1, middle, right, start, end, edge)

    for time, event in enumerate(events):
        edge = tuple(sorted((event.u, event.v)))
        if event.kind == "add":
            if edge in active:
                raise ValueError(f"edge already active at event {time}")
            active[edge] = time
        elif event.kind == "remove":
            if edge not in active:
                raise ValueError(f"edge not active at event {time}")
            interval(1, 0, count, active.pop(edge), time, edge)
    for edge, start in active.items():
        interval(1, 0, count, start, count, edge)

    dsu = RollbackDSU(nodes)
    answers: list[dict] = []

    def visit(index: int, left: int, right: int) -> None:
        before = dsu.snapshot()
        for u, v in tree[index]:
            dsu.union(u, v)
        if right - left == 1:
            event = events[left]
            if event.kind == "query":
                answers.append({"event": left, "u": event.u, "v": event.v,
                                "connected": dsu.connected(event.u, event.v)})
        else:
            middle = (left + right) // 2
            visit(index * 2, left, middle)
            visit(index * 2 + 1, middle, right)
        dsu.rollback(before)

    visit(1, 0, count)
    return answers


def unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON field: {key}")
        value[key] = item
    return value


def main() -> None:
    cli = argparse.ArgumentParser(description="Answer connectivity queries over an edge timeline")
    cli.add_argument("input", type=Path)
    args = cli.parse_args()
    try:
        if args.input.stat().st_size > 5_000_000:
            raise ValueError("input exceeds 5 MB")
        document = json.loads(args.input.read_text(encoding="utf-8"), object_pairs_hook=unique)
        print(json.dumps({"queries": solve(document)}, indent=2))
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        cli.exit(2, f"timelink: {exc}\n")


if __name__ == "__main__":
    main()
