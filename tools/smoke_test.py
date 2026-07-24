from pathlib import Path

import clr_loader
from pythonnet import set_runtime

# runtime.json defines the .NET version. .NET 10 is the current LTS release.
set_runtime(
    clr_loader.get_coreclr(runtime_config=Path(__file__).parent / "runtime.json")
)

import WebView2  # noqa: E402

print(f"{WebView2.__version__=}")

print("Importing WebView2...")

from Microsoft.Web.WebView2.WinForms import WebView2  # noqa: E402

print("Creating Webview2 instance...")
webview2 = WebView2()
print(f"{webview2=}")

print("Done.")
