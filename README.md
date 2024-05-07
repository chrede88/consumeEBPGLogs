# consumeEBPGLogs

This is a small CLI tool created to easily comsume logs from a Raith EBPG electron beam writer.

## Install
It's recommended to install this using [pipx](https://pipx.pypa.io). pipx installs each package in an isolated environment, which mitigates depedency version issues.

```sh
pipx install git+https://github.com/chrede88/comsumeEBPGLogs.git
```

## Usage
The CLI tool takes two flag, one mondatory the other optional.

Use `-f [--file] path/to/log` to point to a logfile.

Pass `-p [--plot]` to open a plot of the chip heightmap created as the chip was written (optional).

Pass `-h [--help]` (only) to print the help page.

```sh
comsumeEBPGLogs -p -f path/to/log
```

## Update
Updating the package using `pipx` is just as easy as installing it.

```sh
pipx upgrade comsumeEBPGLogs
```