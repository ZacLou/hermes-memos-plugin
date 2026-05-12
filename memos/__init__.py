# MemOS memory provider plugin for Hermes
# Implements MemoryProvider ABC
# API docs: https://memos-docs.openmem.net
#
# Config: ~/.hermes/memos.json or env vars
#   api_key      (required)
#   base_url     (default: https://memos.memtensor.cn)
#   user_id      (default: hermes-user)
#   agent_id     (default: hermes)

import sys
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Hermes loads user plugins before hermes-agent is on sys.path.
# Add it so we can import agent.memory_provider and tools.registry.
_hermes_agent = Path.home() / ".hermes" / "hermes-agent"
if _hermes_agent.is_dir() and str(_hermes_agent) not in sys.path:
    sys.path.insert(0, str(_hermes_agent))

import json
import requests

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_config():
    """Load config: env vars first, ~/.hermes/memos.json overrides."""
    from hermes_constants import get_hermes_home

    cfg = {
        "api_key":    os.environ.get("MEMOS_API_KEY", ""),
        "base_url":   os.environ.get("MEMOS_BASE_URL", "https://memos.memtensor.cn"),
        "user_id":    os.environ.get("MEMOS_USER_ID", "hermes-user"),
        "agent_id":   os.environ.get("MEMOS_AGENT_ID", "hermes"),
    }
    path = get_hermes_home() / "memos.json"
    if path.exists():
        try:
            file_cfg = json.loads(path.read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in file_cfg.items() if v})
        except Exception:
            pass
    return cfg


# ---------------------------------------------------------------------------
# Tool schemas (what Hermes sees)
# ---------------------------------------------------------------------------

_PROFILE_SCHEMA = {
    "name": "memos_profile",
    "description": "Retrieve all stored memories about the user. Use at conversation start.",
    "parameters": {"properties": {}, "required": [], "type": "object"},
}

_SEARCH_SCHEMA = {
    "name": "memos_search",
    "description": "Search memories by semantic meaning. Use when you need to recall something the user told you.",
    "parameters": {
        "properties": {
            "query":  {"description": "What to search for.", "type": "string"},
            "top_k": {"description": "Max results (default 10).", "type": "integer"},
        },
        "required": ["query"],
        "type": "object",
    },
}

_CONCLUDE_SCHEMA = {
    "name": "memos_conclude",
    "description": "Store a fact about the user. Use for preferences, corrections, decisions.",
    "parameters": {
        "properties": {
            "conclusion": {"description": "The fact to store.", "type": "string"},
        },
        "required": ["conclusion"],
        "type": "object",
    },
}


# ---------------------------------------------------------------------------
# Circuit breaker: fail-fast after repeated errors
# ---------------------------------------------------------------------------

class _Breaker:
    def __init__(self, threshold=5, cooldown=120):
        self.threshold = threshold
        self.cooldown = cooldown
        self._failures = 0
        self._cooldown_until = 0.0
        self._lock = threading.Lock()

    def check(self):
        with self._lock:
            if self._failures < self.threshold:
                return False
            if time.monotonic() >= self._cooldown_until:
                self._failures = 0
                return False
            return True

    def success(self):
        with self._lock:
            self._failures = 0

    def failure(self):
        with self._lock:
            self._failures += 1
            if self._failures >= self.threshold:
                self._cooldown_until = time.monotonic() + self.cooldown
                logger.warning("MemOS circuit breaker tripped (%d failures)", self._failures)


# ---------------------------------------------------------------------------
# MemOS API helper
# ---------------------------------------------------------------------------

def _api_post(base_url, api_key, endpoint, data, timeout=30):
    resp = requests.post(
        base_url + endpoint,
        headers={"Authorization": "Token " + api_key, "Content-Type": "application/json"},
        json=data,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------

class MemOSMemoryProvider(MemoryProvider):
    def __init__(self):
        self.name = "memos"
        self._cfg = {}
        self._api_key = ""
        self._base_url = ""
        self._user_id = "hermes-user"
        self._agent_id = "hermes"
        self._session_id = ""
        self._breaker = _Breaker()
        self._prefetch_result = ""
        self._prefetch_lock = threading.Lock()
        self._prefetch_thread = None
        self._sync_thread = None

    def is_available(self):
        return bool(_load_config().get("api_key"))

    def get_config_schema(self):
        return [
            {"key": "api_key",  "description": "MemOS API key",        "required": True,  "secret": True},
            {"key": "base_url",  "description": "MemOS API base URL",  "default": "https://memos.memtensor.cn"},
            {"key": "user_id",   "description": "User identifier",      "default": "hermes-user"},
            {"key": "agent_id",  "description": "Agent identifier",    "default": "hermes"},
        ]

    def save_config(self, values, hermes_home):
        path = Path(hermes_home) / "memos.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing.update({k: v for k, v in values.items() if v})
        path.write_text(json.dumps(existing, indent=2))

    # -- lifecycle -----------------------------------------------------------

    def initialize(self, session_id, **kwargs):
        self._cfg = _load_config()
        self._api_key  = self._cfg.get("api_key", "")
        self._base_url = self._cfg.get("base_url", "https://memos.memtensor.cn")
        self._user_id  = kwargs.get("user_id") or self._cfg.get("user_id", "hermes-user")
        self._agent_id = self._cfg.get("agent_id", "hermes")
        self._session_id = session_id or ""

    def system_prompt_block(self):
        return "# MemOS Memory\nActive. User: " + self._user_id + "."

    def shutdown(self):
        for t in (self._prefetch_thread, self._sync_thread):
            if t and t.is_alive():
                t.join(timeout=5.0)

    # -- prefetch (non-blocking memory search before responding) -------------

    def queue_prefetch(self, query, session_id=""):
        if self._breaker.check():
            return
        self._prefetch_thread = threading.Thread(
            target=self._do_prefetch, args=(query,), daemon=True, name="memos-prefetch"
        )
        self._prefetch_thread.start()

    def _do_prefetch(self, query):
        try:
            result = _api_post(self._base_url, self._api_key, "/api/openmem/v1/search/memory", {
                "user_id": self._user_id, "query": query, "top_k": 5,
            })
            memories = (result.get("data") or {}).get("memory_detail_list", [])
            if memories:
                with self._prefetch_lock:
                    self._prefetch_result = "\n".join(
                        "- " + m["memory_value"] for m in memories if m.get("memory_value")
                    )
            self._breaker.success()
        except Exception as e:
            self._breaker.failure()
            logger.debug("MemOS prefetch failed: %s", e)

    def prefetch(self, query, session_id=""):
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=3.0)
        with self._prefetch_lock:
            result = self._prefetch_result
            self._prefetch_result = ""
        return ("## MemOS Memory\n" + result) if result else ""

    # -- sync turn (send conversation to MemOS for server-side extraction) -

    def sync_turn(self, user_content, assistant_content, session_id=""):
        if self._breaker.check():
            return
        self._sync_thread = threading.Thread(
            target=self._do_sync, args=(user_content, assistant_content),
            daemon=True, name="memos-sync"
        )
        self._sync_thread.start()

    def _do_sync(self, user_msg, assistant_msg):
        try:
            _api_post(self._base_url, self._api_key, "/api/openmem/v1/add/message", {
                "user_id": self._user_id,
                "agent_id": self._agent_id,
                "conversation_id": self._session_id or "default",
                "messages": [
                    {"role": "user",      "content": user_msg},
                    {"role": "assistant",  "content": assistant_msg},
                ],
            })
            self._breaker.success()
        except Exception as e:
            self._breaker.failure()
            logger.warning("MemOS sync failed: %s", e)

    # -- tool calls ---------------------------------------------------------

    def get_tool_schemas(self):
        return [_PROFILE_SCHEMA, _SEARCH_SCHEMA, _CONCLUDE_SCHEMA]

    def handle_tool_call(self, tool_name, args, **kwargs):
        if self._breaker.check():
            return json.dumps({"error": "MemOS temporarily unavailable, will retry."})

        try:
            if tool_name == "memos_profile":
                return self._tool_profile()
            elif tool_name == "memos_search":
                return self._tool_search(args)
            elif tool_name == "memos_conclude":
                return self._tool_conclude(args)
        except Exception as e:
            self._breaker.failure()
            return tool_error("MemOS API error: " + str(e))

        return tool_error("Unknown tool: " + tool_name)

    def _tool_profile(self):
        result = _api_post(self._base_url, self._api_key, "/api/openmem/v1/get/memory", {
            "user_id": self._user_id, "page": 1, "size": 50,
        })
        if result.get("code") != 0:
            return tool_error("Failed: " + result.get("message", ""))
        memories = (result.get("data") or {}).get("memory_detail_list", [])
        if not memories:
            return json.dumps({"result": "No memories stored yet."})
        return json.dumps({"result": "\n".join(
            m["memory_value"] for m in memories if m.get("memory_value")
        )})

    def _tool_search(self, args):
        query = args.get("query", "")
        if not query:
            return tool_error("Missing required parameter: query")
        top_k = min(int(args.get("top_k", 10)), 50)
        result = _api_post(self._base_url, self._api_key, "/api/openmem/v1/search/memory", {
            "user_id": self._user_id, "query": query, "top_k": top_k,
        })
        if result.get("code") != 0:
            return tool_error("Search failed: " + result.get("message", ""))
        memories = (result.get("data") or {}).get("memory_detail_list", [])
        if not memories:
            return json.dumps({"result": "No relevant memories found."})
        return json.dumps({"results": [
            {"memory": r["memory_value"], "score": r.get("confidence", 0)}
            for r in memories if r.get("memory_value")
        ], "count": len(memories)})

    def _tool_conclude(self, args):
        conclusion = args.get("conclusion", "")
        if not conclusion:
            return tool_error("Missing required parameter: conclusion")
        _api_post(self._base_url, self._api_key, "/api/openmem/v1/add/message", {
            "user_id":        self._user_id,
            "agent_id":       self._agent_id,
            "conversation_id": self._session_id or "default",
            "messages": [{"role": "user", "content": conclusion}],
        })
        return json.dumps({"result": "Fact stored."})


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

def register(ctx):
    """register_memory_provider"""
    ctx.register_memory_provider(MemOSMemoryProvider())
