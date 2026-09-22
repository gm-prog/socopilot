# GitHub Support ticket — purge cached pull-request refs (paste-ready)

> **How to file:** open <https://support.github.com/request> (or the owner
> account's "Contact GitHub Support" from the repo page), pick *Account or
> repository → Other*, and paste the text below as-is. Only a repository
> owner can file it. This cannot be done via the API — GitHub's cached PR
> refs are not exposed to any REST/GraphQL mutation.

---

**Subject:** History rewrite completed — please purge cached `refs/pull/*` and closed-PR views for `gm-prog/socopilot`

**Body:**

Hello,

We completed a `git filter-repo` history rewrite on `gm-prog/socopilot` to
remove a leaked credential file (`frontend/public/token.txt`, whose token has
also expired) from every commit. The default branch `main` was force-pushed
with the cleaned history and is verified clean (zero trees contain the path).
The stale `master` branch was deleted, and the remaining stale branches are
being deleted as well.

What remains on GitHub's side is outside API reach, so we need your help
purging:

1. The cached pull-request head refs `refs/pull/1/head` … `refs/pull/4/head`
   for this repository. These point at pre-rewrite commits that still contain
   the removed file and are still fetchable even though the corresponding PRs
   (#1–#4) are closed.
2. Any cached views/diffs/patches of the closed pull requests #1–#5
   (e.g. `github.com/gm-prog/socopilot/pull/1/files`) that may render content
   from the pre-rewrite commits.

Please clear these caches / unlink the cached refs so the old commits are no
longer served. We understand GC of orphaned objects happens on GitHub's side
after refs are released — the ask is specifically about the `refs/pull/*`
refs and PR-page caches, which historically require a Support intervention
after a history rewrite.

The repository owner can provide any verification you need.

Thank you.

---

**Reference data (fill in if Support asks):**
- Repository: `gm-prog/socopilot`
- Purge executed: 2026-09-22 (git filter-repo, `--invert-paths --path frontend/public/token.txt`)
- Default branch after rewrite: `main` (verified: 0 commits/0 trees contain the path)
- Closed PRs whose heads predate the rewrite: #1, #2, #3, #4, #5
- Cached head SHAs observed before deletion: `refs/pull/1` → `620c671`, `refs/pull/2` → `2f23782`, `refs/pull/3` → `785085a`, `refs/pull/4` → `68ff070`
