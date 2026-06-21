import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MoomooRuntimePaths:
    root: Path
    logs: Path
    cache: Path
    tmp: Path


class MoomooRuntimeIsolationError(RuntimeError):
    pass


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def configure_moomoo_runtime(project_root: Path | None = None) -> MoomooRuntimePaths:
    root = (project_root or default_project_root()).resolve()
    runtime_root = (root / ".runtime" / "moomoo").resolve()
    paths = MoomooRuntimePaths(
        root=runtime_root,
        logs=(runtime_root / "logs").resolve(),
        cache=(runtime_root / "cache").resolve(),
        tmp=(runtime_root / "tmp").resolve(),
    )

    for path in (paths.root, paths.logs, paths.cache, paths.tmp):
        _ensure_inside(path, runtime_root)
        path.mkdir(parents=True, exist_ok=True)

    sdk_base = str(paths.root)
    os.environ["appdata"] = sdk_base
    os.environ["APPDATA"] = sdk_base
    os.environ["HOME"] = sdk_base
    os.environ["MOOMOO_LOG_DIR"] = str(paths.logs)
    os.environ["MOOMOO_CACHE_DIR"] = str(paths.cache)
    os.environ["TMP"] = str(paths.tmp)
    os.environ["TEMP"] = str(paths.tmp)
    return paths


def _ensure_inside(path: Path, parent: Path) -> None:
    try:
        path.relative_to(parent)
    except ValueError as exc:
        raise MoomooRuntimeIsolationError("moomoo runtime path escaped project runtime") from exc
