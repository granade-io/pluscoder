# Installation


- Requires Python 3.12.
- Requires [llvm](https://apt.llvm.org/)

=== "Any OS"
    ```bash
    bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)"
    ```
=== "MacOS"
    ```bash
    brew install llvm@14
    ```

Install PlusCoder as Python library:

=== "uv"
    ```bash
    uv tool install pluscoder --python 3.12
    ```
=== "pip"
    ```bash
    pip install pluscoder
    ```


This install everything needed to use PlusCoder with different providers.

You can check the installed version with:

```bash
pluscoder --version
```

## Next Steps
- [Quick Start Guide](quick_start.md)
- [Configuration](documentation/configuration.md)
- [CLI Usage](documentation/cli.md)