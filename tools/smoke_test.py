from pathlib import Path

import clr_loader
from pythonnet import set_runtime

# runtime.json defines the .NET version. .NET 10 is the current LTS release.
set_runtime(
    clr_loader.get_coreclr(
        runtime_config=Path(__file__).parent / "runtime.json"
    )
)

import WebView2

print(f"{WebView2.__version__=}")
