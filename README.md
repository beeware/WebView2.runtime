# WebView2.runtime

[<img src="http://beeware.org/static/images/defaultlogo.png" width="72px" alt="Generic BeeWare Logo">](https://beeware.org/)

[![Python Versions](https://img.shields.io/pypi/pyversions/WebView2.runtime.svg)](https://pypi.python.org/pypi/WebView2.runtime) [![PyPI Version](https://img.shields.io/pypi/v/WebView2.runtime.svg)](https://pypi.python.org/pypi/WebView2.runtime) [![Maturity](https://img.shields.io/pypi/status/WebView2.runtime.svg)](https://pypi.python.org/pypi/WebView2.runtime) [![BSD License](https://img.shields.io/pypi/l/WebView2.runtime.svg)](https://github.com/beeware/WebView2.runtime/blob/main/LICENSE) [![Discord server](https://img.shields.io/discord/836455665257021440?label=Discord%20Chat&logo=discord&style=plastic)](https://beeware.org/bee/chat/)

This is the [Microsoft WebView2 runtime](https://www.nuget.org/packages/Microsoft.Web.WebView2) binaries, packaged with a light [Python.NET](http://pythonnet.github.io) wrapper, to enable easy use of WebView2 in Winforms applications.

For details on usage and distribution, see [the Microsoft WebView2 documentation](https://docs.microsoft.com/en-us/microsoft-edge/webview2/)

Before use, the end-user must have the WebView2 Runtime installed. [Details can be found here](https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download-section).

## Usage

Once installed in an environment that also has Python.NET installed, importing the WebView2 package will load the WebView2 assemblies. The `Microsoft.Web.WebView2` libraries can then be imported and used:

    # Load the WebView2 assemblies
    import WebView2

    # Create a WebView2 instance
    from Microsoft.Web.WebView2.WinForms import WebView2

    webview2 = WebView2()

## Updating the binaries

To update the WebView2 binaries, run:

    $ python -m venv venv
    $ source venv/bin/activate
    (venv) $ pip install -U pip
    (venv) $ pip install --group dev
    (venv) $ python tools/update.py 1.0.3967.48

## Community

This binary distribution package is part of the [BeeWare suite](http://beeware.org). You can talk to the community through:

- [@beeware@fosstodon.org on Mastodon](https://fosstodon.org/@beeware)
- [Discord](https://beeware.org/bee/chat/)

We foster a welcoming and respectful community as described in our [BeeWare Community Code of Conduct](http://beeware.org/community/code-of-conduct/).

## Contributing

If you experience problems with this package, [log them on GitHub](https://github.com/beeware/WebView2.runtime/issues). If you want to contribute, please [fork the project](https://github.com/beeware/WebView2.runtime) and [submit a pull request](https://github.com/beeware/WebView2.runtime/pulls).
