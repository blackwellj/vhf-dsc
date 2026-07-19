"""Message clusterer for multi-window decode results."""

from __future__ import annotations

from ..protocol.message import DSCMessage


class MessageClusterer:
    """Cluster and deduplicate decode results from multiple windows.

    When multiple parallel decoders process the same signal,
    they may produce slightly different results. This clusterer
    groups similar messages and selects the best one.
    """

    def __init__(self, time_window_ms: int = 500):
        self.time_window_ms = time_window_ms
        self._clusters: list[list[DSCMessage]] = []

    def add(self, msg: DSCMessage) -> DSCMessage | None:
        """Add a decoded message and return the best cluster representative.

        Args:
            msg: Decoded message

        Returns:
            Best message from the cluster, or None if not yet complete
        """
        cluster = self._find_cluster(msg)

        if cluster is None:
            cluster = [msg]
            self._clusters.append(cluster)
        else:
            cluster.append(msg)

        return self._select_best(cluster)

    def _find_cluster(self, msg: DSCMessage) -> list[DSCMessage] | None:
        """Find an existing cluster that matches this message."""
        for cluster in self._clusters:
            if self._matches_cluster(msg, cluster):
                return cluster
        return None

    def _matches_cluster(self, msg: DSCMessage,
                         cluster: list[DSCMessage]) -> bool:
        """Check if a message matches an existing cluster."""
        if not cluster:
            return False

        rep = cluster[0]

        if msg.mmsi_self != rep.mmsi_self:
            return False
        if msg.mmsi_dest != rep.mmsi_dest:
            return False
        if msg.format_specifier != rep.format_specifier:
            return False
        if msg.category != rep.category:
            return False

        return True

    def _select_best(self, cluster: list[DSCMessage]) -> DSCMessage:
        """Select the best message from a cluster.

        Priority:
        1. Message with valid ECC
        2. Message with most complete data
        3. First message received
        """
        for msg in cluster:
            if msg.is_valid:
                return msg

        best = cluster[0]
        for msg in cluster[1:]:
            if self._is_more_complete(msg, best):
                best = msg

        return best

    def _is_more_complete(self, a: DSCMessage, b: DSCMessage) -> bool:
        """Check if message a has more complete data than b."""
        score_a = sum([
            a.mmsi_self is not None,
            a.mmsi_dest is not None,
            a.position is not None,
            a.telecommand_1 is not None,
            a.telecommand_2 is not None,
        ])
        score_b = sum([
            b.mmsi_self is not None,
            b.mmsi_dest is not None,
            b.position is not None,
            b.telecommand_1 is not None,
            b.telecommand_2 is not None,
        ])
        return score_a > score_b

    def get_all_clusters(self) -> list[DSCMessage]:
        """Get the best message from each cluster."""
        return [self._select_best(c) for c in self._clusters if c]

    def reset(self):
        """Reset all clusters."""
        self._clusters.clear()
