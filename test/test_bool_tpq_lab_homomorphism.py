from unittest import TestCase

from controller.bool_tpq_lab_homomorphism import BoolTPQLabPayloadError, find_bool_tpq_lab_homomorphism


class TestBoolTPQLabHomomorphism(TestCase):
	def test_find_homomorphism_returns_mapping(self):
		source = {
			"root_id": "node_0",
			"nodes": [
				{"id": "node_0", "label": "a"},
				{"id": "node_1", "label": "b"},
			],
			"edges": [
				{"source": "node_0", "target": "node_1", "type": "child"},
			],
		}
		target = {
			"root_id": "node_0",
			"nodes": [
				{"id": "node_0", "label": "a"},
				{"id": "node_1", "label": "b"},
			],
			"edges": [
				{"source": "node_0", "target": "node_1", "type": "child"},
			],
		}

		result = find_bool_tpq_lab_homomorphism(source, target)

		assert result["exists"] is True
		assert result["mapping"][0]["source_id"] == "node_0"
		assert result["mapping"][0]["target_id"] == "node_0"
		assert result["mapping"][1]["source_id"] == "node_1"
		assert result["mapping"][1]["target_id"] == "node_1"
		assert result["highlight_target_ids"] == ["node_0", "node_1"]

	def test_find_homomorphism_reports_failure(self):
		source = {
			"root_id": "node_0",
			"nodes": [
				{"id": "node_0", "label": "a"},
				{"id": "node_1", "label": "c"},
			],
			"edges": [
				{"source": "node_0", "target": "node_1", "type": "child"},
			],
		}
		target = {
			"root_id": "node_0",
			"nodes": [
				{"id": "node_0", "label": "a"},
				{"id": "node_1", "label": "b"},
			],
			"edges": [
				{"source": "node_0", "target": "node_1", "type": "child"},
			],
		}

		result = find_bool_tpq_lab_homomorphism(source, target)

		assert result["exists"] is False
		assert result["mapping"] == []
		assert result["highlight_target_ids"] == []

	def test_find_homomorphism_rejects_wildcard_labels(self):
		payload = {
			"root_id": "node_0",
			"nodes": [
				{"id": "node_0", "label": "*"},
			],
			"edges": [],
		}

		with self.assertRaises(BoolTPQLabPayloadError):
			find_bool_tpq_lab_homomorphism(payload, payload)

