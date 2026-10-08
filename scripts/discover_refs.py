#!/usr/bin/env python
"""Turn `git ls-remote --heads apple/device-management` (on stdin) into a
GitHub Actions build matrix.

`release` is published as release.schema.json. Every seed_* branch gets its own
file, and the newest seed is also published as seed.schema.json. Apple's seed
branch names aren't consistent (seed_OS_27_0, seed_OS-27.2), so "newest" is
decided by the numbers in the name.
"""

import json
import re
import sys


def version(branch: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", branch))


def main() -> None:
    branches = [line.split("refs/heads/", 1)[1].strip() for line in sys.stdin if "refs/heads/" in line]
    seeds = sorted((b for b in branches if b.startswith("seed")), key=version)

    include = []
    if "release" in branches:
        include.append({"ref": "release", "name": "release", "alias": ""})
    for seed in seeds:
        alias = "seed" if seed == seeds[-1] else ""
        include.append({"ref": seed, "name": seed, "alias": alias})
    print(json.dumps({"include": include}))


if __name__ == "__main__":
    main()
