# Development notes

## Starting point

The standalone project starts from skin revision 2.5.3, developed on a Denon
SC Live 4 with VirtualDJ build 8472. The changes focus on layout and the amount
of moving waveform imagery the screen has to update.

The controller's driver, firmware, Denon SDK and USB transport were not modified.
The work did not establish the exact screen-transfer format or measure USB
bandwidth use.

## Hardware checks

The maintainer confirmed track-FX cycling, updated effect names and independent
deck selection in the requested two-deck and four-deck checks. The wider
ECO/SLIM layout and the Key Lock indicator were also confirmed.

The minus-prefixed REMAIN change was built and installed, but its device readout
was not separately confirmed. The included preview uses synthetic track data.

Performance figures in the README are observations while mixing on one setup.
There is no instrumented benchmark. Track content and the rest of the setup can
affect the result.

## Waveform sizes

| View | ECO | SLIM | WIDE |
|---|---:|---:|---:|
| 2D, each main wave | 1168 x 24 | 1168 x 32 | 1168 x 96 |
| 4D, each main wave | 824 x 22 | 824 x 32 | 824 x 48 |

These are XML element dimensions in pixels. They do not measure USB traffic or
predict FPS. In the tested VirtualDJ setup, Beat Jump wraps after 32 beats and
Loop after 64 beats.

## Build output

`tools/build.py` uses the Python standard library. It creates:

```text
dist/
  Denon SCLIVE4 Screen.zip
  SHA256SUMS
  build-info.json
  Denon SCLIVE4 Screen/
    Denon SCLIVE4 Screen.xml
    Denon SCLIVE4 Screen.png
```

The ZIP contains the XML and PNG at its root. Its filename, internal filenames
and native XML identity (`denonsclive4`) are preserved for VirtualDJ's hardware
screen selection.

Fixed ZIP metadata makes repeated builds with the same inputs and toolchain
reproducible. The builder checks XML identity, the PNG header, archive entry
names, CRCs and payload bytes. It does not emulate VirtualDJ.

During the standalone export, the generated XML and PNG were compared byte for
byte with the accepted 2.5.3 skin. Local Windows and Linux builds produced the
same archive. An isolated source copy also built without installed Python
packages. A wrong version tag was rejected before output files were written.

## Releases

The workflow is `.github/workflows/release.yml`. It runs on pushes of `v*` tags
and can be started manually with an existing tag. For manual runs, the workflow
must be present on the repository's default branch.

The tag must match `v` plus the contents of `VERSION`. This check can also be run
locally:

```sh
python tools/build.py --tag v2.5.3
```

The GitHub-hosted Ubuntu worker builds the skin and calls `gh release create`
with the ZIP, checksum and build report as attachments. The workflow grants its
`GITHUB_TOKEN` `contents: write` for publication. It marks tags with a prerelease
suffix, such as `v2.6.0-rc.1`, as prereleases.

`--verify-tag` requires the tag to exist remotely. Publishing an already-used
version fails instead of replacing its release. If a failed upload leaves an
incomplete draft, remove that draft before retrying. Keep published version
tags fixed.

The workflow YAML, Bash syntax and stable/prerelease command arguments were
checked locally using a stub for `gh`. At the time of the initial export, the
workflow had not been run on GitHub and no GitHub release had been published.

References: [GitHub token documentation](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token),
[GitHub CLI release command](https://cli.github.com/manual/gh_release_create).
