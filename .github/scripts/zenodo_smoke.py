"""Exercise the real Zenodo path end to end, which the hermetic tests cannot.

Runs against an empty cache, so every asset it touches is downloaded.
"""
import re

import likingInitiative as L

latest = L.resolve_version("latest")
assert re.fullmatch(r"\d+\.\d+\.\d+", latest), latest
print("latest resolves to", latest)

# Two different pinned versions must each report themselves, not the newest.
for pinned in ("1.6.1", "1.6.2"):
    info = L.release_info(version=pinned)
    assert info["version"] == pinned, (pinned, info["version"])
    d = L.get_dataset("leeholyoak2021", version=pinned)
    assert d.data.height > 0
    print(f"v{pinned}: {info['n_ratings']:,} ratings; leeholyoak2021 has {d.data.height:,} rows")

cached = L.cache_info()["versions"]
assert {"1.6.1", "1.6.2"} <= set(cached), cached

try:
    L.release_info(version="0.0.1")
except L.LikingInitiativeError as exc:
    assert "published versions" in str(exc), exc
    print("unknown version fails with:", exc)
else:
    raise AssertionError("an unknown version did not fail")
