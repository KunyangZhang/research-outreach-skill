#!/usr/bin/env python3
"""定位已有 skill 的入口并检查当前模式需要的文件；不执行或安装依赖。"""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(mode="research", roots=None):
    if roots is None:
        codex_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        roots = [codex_root / "skills", Path.home() / ".agents" / "skills"]
    manifest = json.loads((ROOT / "dependencies.json").read_text(encoding="utf-8"))
    results = []
    missing = []
    for dependency in manifest["skills"]:
        name = dependency["name"]
        location = next((root / name for root in roots if (root / name / "SKILL.md").is_file()), None)
        required = mode in dependency["required_for"]
        result = {"name": name, "required": required, "available": location is not None,
                  "repository": dependency["repository"], "install_path": dependency["path"],
                  "tested_ref": dependency.get("tested_ref")}
        if location:
            result["entrypoint"] = str(location / "SKILL.md")
            version = location / "VERSION"
            result["version"] = version.read_text().strip() if version.is_file() else "unknown"
            package_manifest = location / "manifest.json"
            if result["version"] == "unknown" and package_manifest.is_file():
                try:
                    result["version"] = json.loads(package_manifest.read_text()).get("adapter_version", "unknown")
                except (ValueError, OSError):
                    result["version"] = "unknown"
            result["version_status"] = "tested" if result["version"] == dependency.get("tested_version") else "inspect-router"
            workflow = dependency.get("workflow")
            if workflow:
                result["workflow"] = str(location / workflow)
                result["workflow_available"] = (location / workflow).is_file()
                result["mode"] = dependency["modes"].get(mode)
                if required and not result["workflow_available"]:
                    missing.append(name + ":workflow")
        elif required:
            missing.append(name)
        results.append(result)
    return {"mode": mode, "ready": not missing, "missing": missing, "skills": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["research", "papers", "fact-check", "resume", "mail"], default="research")
    parser.add_argument("--skills-root", action="append", type=Path,
                        help="额外 skill 根目录；指定时仅检查这些目录")
    args = parser.parse_args()
    result = check(args.mode, args.skills_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()
