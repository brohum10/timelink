# TimeLink

**Was this network connected at that moment?** TimeLink answers connectivity questions across a timeline of edge additions and removals. It uses a segment tree over time and a disjoint-set union structure that can roll back changes.

Run with Python 3.12+ and no dependencies:

```sh
python timelink.py examples/network.json
```

The example starts with a route from `api` to `worker`, removes a link, then restores it. Queries return `true`, `false`, `false`, `true` as the network changes.

An active edge spans an interval of event positions. A segment tree assigns each interval to a small number of time ranges. Traversing that tree adds the relevant edges to a union-find structure; when traversal returns, it rolls the structure back to its earlier snapshot. This avoids rebuilding the whole graph for each query. The implementation uses union by size and deliberately omits path compression so rollback remains simple.

Edges are undirected and can be active at most once. Removing an inactive edge or adding one twice is an error. Event indexes are zero-based. Node names must be distinct; self-edge changes are rejected. This is an offline analysis tool: the complete event timeline must be available before solving. For `E` events and `N` nodes, the segment-tree assignment uses O(E log E) stored edge references; processing uses roughly O(E log E log N) time and O(E log E + N) memory. It does not control a real network.

Built with AI assistance as a learning project. MIT licensed.
