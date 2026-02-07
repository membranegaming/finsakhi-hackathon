"""
Story Engine — Loads and indexes branching story data from stories.json
for the FinGame RPG module.
"""

import json
import os
from typing import Dict, Optional
from pathlib import Path

STORY_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "stories.json"


class StoryEngine:
    _stories: Dict = {}
    _paths: Dict[str, Dict] = {}          # path_id -> path_data
    _nodes: Dict[str, Dict[str, Dict]] = {}  # path_id -> {node_id -> node_data}
    _characters: Dict[str, Dict] = {}      # character_id -> character_data

    @classmethod
    def load_stories(cls):
        if not STORY_FILE.exists():
            print(f"[FinGame] Story file not found: {STORY_FILE}")
            return

        with open(STORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            cls._stories = data

            # Index characters
            if "characters" in data:
                cls._characters = data["characters"]

            # Index paths
            if "paths" in data:
                for path in data["paths"]:
                    p_id = path["path_id"]
                    cls._paths[p_id] = path
                    cls._nodes[p_id] = {}
                    for node in path["nodes"]:
                        cls._nodes[p_id][node["node_id"]] = node

            # Fallback for old single-story structure
            elif "nodes" in data:
                p_id = data.get("path_id", "default")
                cls._paths[p_id] = data
                cls._nodes[p_id] = {n["node_id"]: n for n in data["nodes"]}

        print(f"[FinGame] Stories loaded: {len(cls._paths)} paths, {len(cls._characters)} characters")

    @classmethod
    def resolve_text(cls, value, language: str = "english"):
        """Resolve bilingual text: if dict with english/hindi keys, pick by language; else return as-is."""
        if isinstance(value, dict):
            return value.get(language, value.get("english", str(value)))
        return value if value else ""

    @classmethod
    def get_available_paths(cls, language: str = "english"):
        """Return list of available story paths with metadata"""
        paths = []
        for p_id, p_data in cls._paths.items():
            paths.append({
                "path_id": p_id,
                "title": cls.resolve_text(p_data.get("title", p_id), language),
                "description": cls.resolve_text(p_data.get("description", ""), language),
                "protagonist": p_data.get("protagonist", ""),
            })
        return paths

    @classmethod
    def get_start_node(cls, path_id: str) -> Optional[Dict]:
        nodes = cls._nodes.get(path_id)
        if not nodes:
            return None
        path_data = cls._paths.get(path_id)
        if path_data and "nodes" in path_data:
            sorted_nodes = sorted(path_data["nodes"], key=lambda k: k.get("sequence", 0))
            if sorted_nodes:
                return sorted_nodes[0]
        return None

    @classmethod
    def get_node(cls, path_id: str, node_id: str) -> Optional[Dict]:
        return cls._nodes.get(path_id, {}).get(node_id)

    @classmethod
    def get_next_node(cls, path_id: str, current_sequence: int) -> Optional[Dict]:
        path_data = cls._paths.get(path_id)
        if not path_data:
            return None
        next_seq = current_sequence + 1
        for node in path_data["nodes"]:
            if node.get("sequence") == next_seq:
                return node
        return None

    @classmethod
    def get_character(cls, character_id: str) -> Optional[Dict]:
        return cls._characters.get(character_id)
