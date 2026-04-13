# Installation

## Requirements

- Python 3.10 or later
- `pip`

## Install from a release

1. Go to the [Releases page](../../releases) and download the `.whl` file from the latest release.

2. Install it with pip:
```
pip install ce_cli-<version>-py3-none-any.whl
```

3. Verify the installation:
```
ce --help
```

## Install from source

```
git clone https://github.com/CredentialEngine/ce-cli.git
cd ce-cli
pip install -e .
```

## Upgrading

Download the `.whl` from the new release and re-run:
```
pip install --upgrade ce_cli-<version>-py3-none-any.whl
```
