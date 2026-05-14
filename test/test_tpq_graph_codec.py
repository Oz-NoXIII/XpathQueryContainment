from unittest import TestCase

from controller.tpq_graph_codec import booleanize_graph_payload, graph_payload_to_tpq, tpq_to_graph_payload
from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery


class TestTPQGraphCodec(TestCase):
	def _build_sample_tpq(self):
		root = QueryNode("root")
		output_leaf = QueryNode("out")
		plain_leaf = QueryNode("plain")
		root.add_child(output_leaf)
		root.add_descendant(plain_leaf)
		tpq = TreePatternQuery(root)
		tpq.set_output_nodes(root, output_leaf)
		tpq.set_nodes()
		return tpq

	def test_tpq_to_graph_payload_serializes_structure_and_roles(self):
		tpq = self._build_sample_tpq()

		payload = tpq_to_graph_payload(tpq)

		assert payload["root_id"] == "node_0"
		assert payload["is_boolean"] is False
		assert [node["label"] for node in payload["nodes"]] == ["root", "out", "plain"]
		assert [node["depth"] for node in payload["nodes"]] == [0, 1, 1]
		assert payload["nodes"][0]["roles"] == ["u1"]
		assert payload["nodes"][1]["roles"] == ["u2"]
		assert {edge["type"] for edge in payload["edges"]} == {"child", "descendant"}

	def test_graph_payload_to_tpq_rebuilds_tree_and_outputs(self):
		payload = {
			"root_id": "node_0",
			"nodes": [
				{"id": "node_0", "label": "root", "roles": ["u1"], "is_root": True},
				{"id": "node_1", "label": "out", "roles": ["u2"]},
				{"id": "node_2", "label": "plain", "roles": []},
			],
			"edges": [
				{"source": "node_0", "target": "node_1", "type": "child"},
				{"source": "node_0", "target": "node_2", "type": "descendant"},
			],
			"is_boolean": False,
		}

		tpq = graph_payload_to_tpq(payload)

		assert tpq.get_root().get_label() == "root"
		assert [child.get_label() for child in tpq.get_root().get_children()] == ["out"]
		assert [descendant.get_label() for descendant in tpq.get_root().get_descendants()] == ["plain"]
		assert tpq.get_output_nodes()[0].get_label() == "root"
		assert tpq.get_output_nodes()[1].get_label() == "out"

	def test_booleanize_graph_payload_attaches_boolean_sentinels(self):
		payload = {
			"root_id": "node_0",
			"nodes": [
				{"id": "node_0", "label": "root", "roles": ["u1"], "is_root": True},
				{"id": "node_1", "label": "out", "roles": ["u2"]},
				{"id": "node_2", "label": "plain", "roles": []},
			],
			"edges": [
				{"source": "node_0", "target": "node_1", "type": "child"},
				{"source": "node_0", "target": "node_2", "type": "descendant"},
			],
			"is_boolean": False,
		}

		booleanized_payload = booleanize_graph_payload(payload)
		labels = [node["label"] for node in booleanized_payload["nodes"]]

		assert booleanized_payload["is_boolean"] is True
		assert "o1" in labels
		assert "o2" in labels
		assert "*" in labels


