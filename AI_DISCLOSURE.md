# AI disclosure

Wendy was developed through an iterative collaboration between its human
maintainer and **OpenAI Codex**, with substantial AI assistance.

## AI contributions

AI assisted with researching VirtualDJ's skin and scripting interfaces,
investigating reported screen-performance issues, designing the layout,
generating and revising code, preparing documentation, and implementing the
cross-platform builder and GitHub Actions release workflow. AI also used tools
to run local builds, compare generated files and check static layout geometry.

## Human involvement and verification

The maintainer supplied the requirements, made usability decisions and tested
successive versions with VirtualDJ on a real Denon SC Live 4. Their observations
and feedback guided the changes and identified issues that static checks missed.

Hardware observations come from that human testing. Reported FPS figures are
subjective estimates from one setup. Automated checks cover specific properties
such as layout geometry, archive contents and repeatable builds; they do not
establish performance or correctness on every device and software configuration.
The README records the validation scope and outstanding checks.

## Assets and previews

The sprite sheet and native system-dialog definitions were retained from the
supplied stock screen package; see [NOTICE.md](NOTICE.md). They were not created
by AI for Wendy. The included preview is rendered by code using synthetic track
data, rather than captured from the controller.

The README uses a logo supplied by the maintainer.