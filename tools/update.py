"""Update the bundled Microsoft.Web.WebView2 DLLs from a NuGet package.

Given a version tag (e.g. ``1.0.4078.44``), this script downloads the
``Microsoft.Web.WebView2`` NuGet package for that version and refreshes the
DLLs that are vendored into ``src/WebView2``:

* ``src/WebView2/Microsoft.Web.WebView2.*.dll`` are updated from the package's
  ``lib/net462`` folder.
* ``src/WebView2/runtimes/*/native/WebView2Loader.dll`` are updated from the
  package's matching ``runtimes/*/native`` folders.

Usage::

    python tools/update.py 1.0.4078.44
"""

import argparse
import io
import sys
import zipfile
from pathlib import Path

import httpx2

# The NuGet package ID for the WebView2 SDK.
PACKAGE_ID = "Microsoft.Web.WebView2"

# The flat-container download URL for a specific version of a NuGet package.
# This returns the raw .nupkg (a ZIP archive).
DOWNLOAD_URL = "https://www.nuget.org/api/v2/package/{package_id}/{version}"

# The folder inside the package that contains the managed assemblies to vendor.
LIB_FOLDER = "lib/net462"

# The root folder inside the package that contains the per-architecture native
# loaders.
RUNTIMES_FOLDER = "runtimes"

# The native loader filename shipped for each runtime.
LOADER_NAME = "WebView2Loader.dll"

# The repository's ``src/WebView2`` directory (relative to this script).
WEBVIEW2_DIR = Path(__file__).resolve().parent.parent / "src" / "WebView2"


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


def update(version):
    """Update all vendored WebView2 DLLs to the given version.

    :param version: The version tag to update to (e.g. ``1.0.4078.44``).
    """
    package = download_package(version)
    with package:
        update_managed_dlls(package)
        update_native_loaders(package)
    print(f"Updated WebView2 DLLs to {version}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version",
        help="The WebView2 NuGet package version tag (e.g. 1.0.4078.44).",
    )
    args = parser.parse_args()

    try:
        update(args.version)
    except (FileNotFoundError, OSError, httpx2.HTTPError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
