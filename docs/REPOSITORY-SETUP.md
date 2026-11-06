# Repository setup

## Publish the first build

The release workflow runs on version tags. A normal push to `main` does not
publish a release. For the current `VERSION` value, create and push `v2.5.3`.

In GitHub Desktop, commit and push your changes, open **History**, right-click
the release commit and choose **Create Tag...**. Enter `v2.5.3`, create the tag
and use **Push origin** if it has not been pushed automatically.

Or run from the repository directory:

```sh
git tag -a v2.5.3 -m "Wendy 2.5.3"
git push origin v2.5.3
```

Watch [Build and publish Wendy](https://github.com/AdysonLN/wendy/actions/workflows/release.yml).
Once it succeeds, the installable ZIP appears on the repository's Releases page.
The suggested Python workflows shown by GitHub are optional templates; this
project already has its own workflow.

## Keep direct pushes for the owner

The public repository is intended to accept outside changes through forks and
pull requests. Keep write access reserved for the owner. Outside contributors
can fork the repository without being invited as collaborators.

The prepared [.github/rulesets/main.json](../.github/rulesets/main.json) requires
pull requests into `main`, one approval and resolved review threads for actors
without bypass access. It also blocks branch deletion and force updates for
those actors. Repository administrators have **Always allow** bypass, preserving
the owner's direct pushes. Only grant administrator access to people who should
have the same bypass rights.

To apply it on GitHub:

1. Open **Settings -> Rules -> Rulesets** and import the JSON using
   **New ruleset -> Import a ruleset**.
2. Before saving, confirm the target is `main`, enforcement is **Active**, and
   the bypass entry is **Repository admin -> Always allow**. Remove any other
   bypass entries you do not intend to grant.
3. Save the ruleset. Keep other users out of the repository's write-access list.

The JSON is a configuration template: committing it does not enable protection.
It must be imported and saved in GitHub settings. Its administrator bypass is
for this personal-repository setup. It does not restrict PR source repositories
on its own: the fork-based contribution path comes from withholding write access
from other users. Giving someone write access would also let them create an
in-repository branch and propose a PR from that branch.

References: [GitHub Desktop tags](https://docs.github.com/en/desktop/managing-commits/managing-tags-in-github-desktop),
[GitHub rulesets and bypass settings](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository).
