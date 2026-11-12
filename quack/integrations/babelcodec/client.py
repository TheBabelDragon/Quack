"""Python-facing BabelCodec client via subprocess + JSON-lines worker.

Optional: Quack works without Node.js or BabelCodec. Calling the client
without them raises BabelCodecUnavailable with an actionable message.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional

from .protocol import (
    ALLOWED_OPS,
    CONTRACT,
    DEFAULT_TIMEOUT_S,
    FEATURE_VECTOR_DOMAIN,
    MAX_REQUEST_BYTES,
)


class BabelCodecError(RuntimeError):
    """Protocol or validation failure from the BabelCodec worker."""

    def __init__(self, message: str, *, code: str = "ERROR", detail: Any = None):
        super().__init__(message)
        self.code = code
        self.detail = detail


class BabelCodecUnavailable(BabelCodecError):
    """Node.js or BabelCodec checkout is not available."""


def _worker_path() -> Path:
    return Path(__file__).resolve().parent / "worker.mjs"


def _find_node() -> str:
    node = shutil.which("node")
    if not node:
        raise BabelCodecUnavailable(
            "Node.js not found on PATH; install Node >= 18 to use BabelCodec interop",
            code="NODE_MISSING",
        )
    return node


def _babelcodec_root() -> str:
    root = os.environ.get("BABELCODEC_ROOT", "").strip()
    if not root:
        raise BabelCodecUnavailable(
            "BABELCODEC_ROOT is not set; point it at a local BabelCodec checkout "
            "(>= 0.12.1) to enable interop",
            code="BABELCODEC_ROOT_MISSING",
        )
    p = Path(root)
    if not p.is_dir():
        raise BabelCodecUnavailable(
            f"BABELCODEC_ROOT is not a directory: {root}",
            code="BABELCODEC_ROOT_INVALID",
        )
    if not (p / "package.json").is_file():
        raise BabelCodecUnavailable(
            f"BABELCODEC_ROOT has no package.json: {root}",
            code="BABELCODEC_ROOT_INVALID",
        )
    return str(p.resolve())


class BabelCodecClient:
    """Thin client over the Node worker. One request per subprocess call."""

    def __init__(
        self,
        *,
        babelcodec_root: Optional[str] = None,
        node_bin: Optional[str] = None,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ):
        self._root = babelcodec_root
        self._node = node_bin
        self._timeout = float(timeout_s)
        self._worker = _worker_path()
        if not self._worker.is_file():
            raise BabelCodecUnavailable(
                f"worker.mjs missing at {self._worker}",
                code="WORKER_MISSING",
            )

    def _resolve(self) -> tuple[str, str]:
        node = self._node or _find_node()
        root = self._root or _babelcodec_root()
        return node, root

    def call(self, op: str, payload: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        if op not in ALLOWED_OPS:
            raise BabelCodecError(f"op not allowed: {op}", code="OP_DENIED")

        node, root = self._resolve()
        req_id = str(uuid.uuid4())
        request = {
            "contract": CONTRACT,
            "id": req_id,
            "op": op,
            "payload": dict(payload or {}),
        }
        body = json.dumps(request, separators=(",", ":"), ensure_ascii=False)
        if len(body.encode("utf-8")) > MAX_REQUEST_BYTES:
            raise BabelCodecError("request exceeds size limit", code="REQUEST_TOO_LARGE")

        env = os.environ.copy()
        env["BABELCODEC_ROOT"] = root

        try:
            proc = subprocess.run(
                [node, str(self._worker)],
                input=body.encode("utf-8"),
                capture_output=True,
                timeout=self._timeout,
                env=env,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise BabelCodecError(
                f"BabelCodec worker timed out after {self._timeout}s",
                code="TIMEOUT",
            ) from e
        except FileNotFoundError as e:
            raise BabelCodecUnavailable(
                f"failed to execute node worker: {e}",
                code="NODE_MISSING",
            ) from e

        stdout = proc.stdout.decode("utf-8", errors="replace").strip()
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()

        if not stdout:
            raise BabelCodecError(
                f"worker produced no stdout (exit={proc.returncode})"
                + (f": {stderr}" if stderr else ""),
                code="EMPTY_RESPONSE",
                detail={"stderr": stderr, "returncode": proc.returncode},
            )

        line = stdout.splitlines()[-1]
        try:
            resp = json.loads(line)
        except json.JSONDecodeError as e:
            raise BabelCodecError(
                f"worker returned invalid JSON: {e}",
                code="BAD_RESPONSE",
                detail={"stdout": stdout[:500], "stderr": stderr[:500]},
            ) from e

        if not isinstance(resp, dict) or resp.get("contract") != CONTRACT:
            raise BabelCodecError(
                "worker response missing or wrong contract",
                code="BAD_RESPONSE",
                detail=resp,
            )

        if not resp.get("ok"):
            err = resp.get("error") or {}
            raise BabelCodecError(
                err.get("message") or "worker reported failure",
                code=err.get("code") or "WORKER_ERROR",
                detail={"stderr": stderr, "response": resp},
            )

        result = resp.get("result")
        if not isinstance(result, dict):
            raise BabelCodecError(
                "worker ok response missing result object",
                code="BAD_RESPONSE",
                detail=resp,
            )
        return result

    def health(self) -> dict[str, Any]:
        return self.call("health")

    def validate_feature_vector(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        return self.call("validate_feature_vector", {"features": features})

    def canonicalize(self, value: Any) -> dict[str, Any]:
        return self.call("canonicalize", {"value": value})

    def content_hash(
        self,
        value: Any,
        *,
        domain: str = FEATURE_VECTOR_DOMAIN,
    ) -> dict[str, Any]:
        return self.call("content_hash", {"domain": domain, "value": value})

    def validate_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        return self.call("validate_event", {"event": dict(event)})
