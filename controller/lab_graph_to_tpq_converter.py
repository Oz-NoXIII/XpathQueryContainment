"""
Converter module for transforming BoolTPQ_Lab graph payloads into TreePatternQuery objects.

This module provides convenience functions to work with graphically-created graphs
using proper TreePatternQuery instances instead of raw LabGraph payloads.

The core conversion logic is delegated to tpq_graph_codec which handles the full
conversion between payloads and TreePatternQuery objects.
"""

from typing import Any

from model.tree_pattern_query import TreePatternQuery
from controller.tpq_graph_codec import graph_payload_to_tpq, tpq_to_graph_payload


def convert_lab_graph_payload_to_tpq(payload: Any) -> TreePatternQuery:
	"""
	Convert a graphical editor payload into a TreePatternQuery object.

	This is a convenience wrapper around graph_payload_to_tpq that clearly indicates
	the conversion is from the graphical builder's LabGraph-like format to the
	internal TreePatternQuery model.

	Args:
		payload: The graph payload from the graphical editor (dict)

	Returns:
		TreePatternQuery: A properly constructed TreePatternQuery with QueryNode hierarchy

	Raises:
		GraphPayloadError: If the payload cannot be validated or converted
	"""
	return graph_payload_to_tpq(payload)


def convert_tpq_to_lab_graph_payload(tpq: TreePatternQuery) -> dict[str, Any]:
	"""
	Convert a TreePatternQuery object into a graph payload for the graphical editor.

	This is a convenience wrapper around tpq_to_graph_payload.

	Args:
		tpq: The TreePatternQuery to convert

	Returns:
		dict: A graph payload compatible with the graphical editor
	"""
	return tpq_to_graph_payload(tpq)


