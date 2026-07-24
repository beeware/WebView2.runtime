"""Update the bundled Microsoft.Web.WebView2 DLLs from a NuGet package.

Given a version tag (e.g. ``1.0.4078.44``), this script downloads the
``Microsoft.Web.WebView2`` NuGet package for that version and refreshes the
DLLs that are vendored into ``src/WebView2``:

* ``src/WebView2/Microsoft.Web.WebView2.*.dll`` are updated from the package's
  ``lib/net462`` folder.
* ``src/WebView2/runtimes/*/native/WebView2Loader.dll`` are updated from the
  package's matching ``runtimes/*/native`` folders.
* ``LICENSE.WebView2`` in the repository root is updated from the package's
  root ``LICENSE.txt``.

If no version is provided, the script queries NuGet for the latest stable
release and compares it against the most recent ``v*`` git tag. If NuGet has a
newer stable release, an update is generated for that release; otherwise the
script reports that the vendored version is already up to date.

Usage::

    python tools/update.py 1.0.4078.44
    python tools/update.py
"""

import argparse
import io
import subprocess
import sys
import zipfile
from pathlib import Path

import httpx2

# The NuGet package ID for the WebView2 SDK.
PACKAGE_ID = "Microsoft.Web.WebView2"

# The flat-container download URL for a specific version of a NuGet package.
# This returns the raw .nupkg (a ZIP archive).
DOWNLOAD_URL = "https://www.nuget.org/api/v2/package/{package_id}/{version}"

# The flat-container index that lists every published version of a package.
VERSIONS_URL = "https://api.nuget.org/v3-flatcontainer/{package_id}/index.json"

# The folder inside the package that contains the managed assemblies to vendor.
LIB_FOLDER = "lib/net462"

# The root folder inside the package that contains the per-architecture native
# loaders.
RUNTIMES_FOLDER = "runtimes"

# The native loader filename shipped for each runtime.
LOADER_NAME = "WebView2Loader.dll"

# The license file at the root of the NuGet package.
PACKAGE_LICENSE = "LICENSE.txt"

# The repository's ``src/WebView2`` directory (relative to this script).
WEBVIEW2_DIR = Path(__file__).resolve().parent.parent / "src" / "WebView2"

# The repository root (relative to this script).
REPO_ROOT = Path(__file__).resolve().parent.parent

# The vendored copy of the WebView2 license in the repository root.
REPO_LICENSE = REPO_ROOT / "LICENSE.WebView2"


def version_key(version):
    """Convert a dotted version string into a comparable tuple of integers.

    :param version: A dotted version string (e.g. ``1.0.4078.44``).
    :returns: A tuple of integers suitable for ordering comparisons.
    """
    return tuple(int(part) for part in version.split("."))


def latest_stable_version():
    """Return the latest stable ``Microsoft.Web.WebView2`` release on NuGet.

    Prerelease versions (those with a ``-prerelease`` style suffix) are
    ignored.

    :returns: The latest stable version string (e.g. ``1.0.4078.44``).
    """
    url = VERSIONS_URL.format(package_id=PACKAGE_ID.lower())
    print(f"Querying NuGet for available versions from {url} ...")
    response = httpx2.get(url, follow_redirects=True)
    response.raise_for_status()
    versions = response.json()["versions"]

    # Stable releases contain only digits and dots; anything with a suffix
    # (e.g. "-prerelease") is a prerelease and is excluded.
    stable = [
        version
        for version in versions
        if all(part.isdigit() for part in version.split("."))
    ]
    if not stable:
        raise RuntimeError("No stable versions found on NuGet.")

    latest = max(stable, key=version_key)
    print(f"Latest stable release on NuGet is {latest}.")
    return latest


def current_version():
    """Return the currently vendored version from the most recent git tag.

    Release tags are of the form ``v{version}`` (e.g. ``v1.0.4022.49``).

    :returns: The current version string, or ``None`` if there are no tags.
    """
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tags = [line for line in result.stdout.splitlines() if line.startswith("v")]
    if not tags:
        return None
    return tags[0].removeprefix("v")


def download_package(version):
    """Download the NuGet package for the given version.

    :param version: The version tag to download (e.g. ``1.0.4078.44``).
    :returns: A :class:`zipfile.ZipFile` opened over the downloaded package.
    """
    url = DOWNLOAD_URL.format(package_id=PACKAGE_ID, version=version)
    print(f"Downloading {PACKAGE_ID} {version} from {url} ...")
    # The download URL redirects to the flat-container CDN, so redirects must
    # be followed.
    response = httpx2.get(url, follow_redirects=True)
    response.raise_for_status()
    data = response.content
    print(f"Downloaded {len(data)} bytes.")
    return zipfile.ZipFile(io.BytesIO(data))


def update_managed_dlls(package):
    """Update the vendored ``Microsoft.Web.WebView2.*.dll`` assemblies.

    Only the assemblies that already exist in ``src/WebView2`` are updated, so
    the set of vendored DLLs is preserved.

    :param package: The opened NuGet package archive.
    """
    for dll in sorted(WEBVIEW2_DIR.glob("Microsoft.Web.WebView2.*.dll")):
        source = f"{LIB_FOLDER}/{dll.name}"
        print(f"Updating {dll.name} from {source} ...")
        try:
            data = package.read(source)
        except KeyError as exc:
            raise FileNotFoundError(
                f"{source} not found in the NuGet package."
            ) from exc
        dll.write_bytes(data)


def update_native_loaders(package):
    """Update the per-architecture ``WebView2Loader.dll`` native loaders.

    Only the runtimes that already exist under ``src/WebView2/runtimes`` are
    updated.

    :param package: The opened NuGet package archive.
    """
    runtimes_dir = WEBVIEW2_DIR / RUNTIMES_FOLDER
    for native_dir in sorted(runtimes_dir.glob("*/native")):
        runtime = native_dir.parent.name
        loader = native_dir / LOADER_NAME
        source = f"{RUNTIMES_FOLDER}/{runtime}/native/{LOADER_NAME}"
        print(f"Updating {runtime}/{LOADER_NAME} from {source} ...")
        try:
            data = package.read(source)
        except KeyError as exc:
            raise FileNotFoundError(
                f"{source} not found in the NuGet package."
            ) from exc
        loader.write_bytes(data)


def update_license(package):
    """Update the vendored WebView2 license from the package.

    :param package: The opened NuGet package archive.
    """
    print(f"Updating {REPO_LICENSE.name} from {PACKAGE_LICENSE} ...")
    try:
        data = package.read(PACKAGE_LICENSE)
    except KeyError as exc:
        raise FileNotFoundError(
            f"{PACKAGE_LICENSE} not found in the NuGet package."
        ) from exc
    REPO_LICENSE.write_bytes(data)


def update(version):
    """Update all vendored WebView2 DLLs to the given version.

    :param version: The version tag to update to (e.g. ``1.0.4078.44``).
    """
    package = download_package(version)
    with package:
        update_managed_dlls(package)
        update_native_loaders(package)
        update_license(package)
    print(f"Updated WebView2 DLLs to {version}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version",
        nargs="?",
        help=(
            "The WebView2 NuGet package version tag (e.g. 1.0.4078.44). "
            "If omitted, the latest stable release is used, and an update is "
            "only generated if it is newer than the most recent git tag."
        ),
    )
    args = parser.parse_args()

    try:
        if args.version:
            update(args.version)
        else:
            latest = latest_stable_version()
            current = current_version()
            if current is None:
                print("No existing release tag found; updating to latest.")
            elif version_key(latest) <= version_key(current):
                print(
                    f"Vendored version {current} is already up to date "
                    f"(latest stable is {latest}); nothing to do."
                )
                return
            else:
                print(f"Updating from {current} to {latest}.")
            update(latest)
    except (FileNotFoundError, OSError, RuntimeError, httpx2.HTTPError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"Error: git command failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
