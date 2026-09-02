"""Mirror one published release of the database from Zenodo into a directory
shaped like a locally built release, so the hermetic test suite can run
against real, checksummed release files.

    python .github/scripts/fetch_release.py 1.6.2 release

Standard library only, so it runs before the package's dependencies exist.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://zenodo.org/api"
CONCEPT_REC = "22216442"
TRANSIENT = {429, 500, 502, 503, 504}


def get(url: str, tries: int = 6) -> bytes:
    delay = 2.0
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=300) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in TRANSIENT or attempt == tries - 1:
                raise
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
        time.sleep(delay)
        delay *= 2
    raise RuntimeError("unreachable")


def record_for(version: str) -> dict:
    query = urllib.parse.urlencode(
        {"q": f"conceptrecid:{CONCEPT_REC}", "all_versions": "true", "size": 25}
    )
    url = f"{API}/records?{query}"
    published = []
    while url:
        page = json.loads(get(url))
        for hit in page["hits"]["hits"]:
            found = hit["metadata"].get("version")
            published.append(found)
            if found == version:
                return hit
        url = page.get("links", {}).get("next")
    sys.exit(f"no release {version} on Zenodo; published: {sorted(published)}")


def main(version: str, dest: Path) -> None:
    record = record_for(version)
    entries = json.loads(get(f"{API}/records/{record['id']}/files"))["entries"]
    fetched = skipped = 0
    for entry in entries:
        expected = entry["checksum"].split(":", 1)[1]
        # Zenodo's file store is flat; nested release paths were uploaded with
        # "/" replaced by "__".
        target = dest / entry["key"].replace("__", "/")
        if target.exists() and hashlib.md5(target.read_bytes()).hexdigest() == expected:
            skipped += 1
            continue
        data = get(entry["links"]["content"])
        actual = hashlib.md5(data).hexdigest()
        if actual != expected:
            sys.exit(f"{entry['key']}: checksum {actual} != {expected}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        fetched += 1
    catalog = json.loads((dest / "catalog.json").read_text(encoding="utf-8"))
    if catalog["release"]["version"] != version:
        sys.exit(f"catalog says {catalog['release']['version']}, expected {version}")
    print(f"release {version} (record {record['id']}): {fetched} fetched, "
          f"{skipped} already present, {len(entries)} files in {dest}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], Path(sys.argv[2]))
