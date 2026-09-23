# GitHub Support ticket — purge cached pull-request refs (paste-ready)

> **How to file:** open <https://support.github.com/request> (or the owner
> account's "Contact GitHub Support" from the repo page), pick *Account or
> repository → Other*, and paste the text below as-is. Only a repository
> owner can file it. This cannot be done via the API — GitHub's cached PR
> refs are not exposed to any REST/GraphQL mutation.

---

**Subject:** History rewrite completed (second purge) — please purge cached `refs/pull/*` and closed-PR views for `gm-prog/socopilot`

**Body:**

Hello,

We completed two `git filter-repo` history rewrites on `gm-prog/socopilot` to
remove a leaked credential (expired JWT) from every branch.

**First purge (2026-09-22):** `git filter-repo --invert-paths --path frontend/public/token.txt`
removed that one path. It left the same blob reachable at `.soc_token` because
the check was path-based. Verification by path claimed "main is clean" but
verification by blob SHA showed the secret survived.

**Second purge (2026-09-23):** `git filter-repo --strip-blobs-with-ids /tmp/strip-blobs.txt --force`
where `/tmp/strip-blobs.txt` contained the leaked blob SHA
`b848f4c67b2635dcfd23b0107072eba560b7aeb4` plus three repomix-output blobs that
embedded the same JWT (`37e1584a99e3e91989a4462842ff8b4eee95bb5d`,
`810cb38876477b74799de8b41970c077689aa86b`,
`bee9402d46abc32296fd645f84d1664bbbcdd137`). The strip was by blob ID, not by
path, so all occurrences were removed regardless of filename.

After the second purge:

- `main` is verified clean by blob SHA:
  `git rev-list --objects origin/main | grep b848f4c67b2635dcfd23b0107072eba560b7aeb4` → no output
  `git rev-list --objects origin/main | grep -c 'frontend/public/token.txt'` → 0
  `git rev-list --objects origin/main | grep -c '\.soc_token'` → 0
- All branch refs were rewritten, including `alerts-page-store-migration`
  (previously retained, now also purged). Heads after rewrite:
  `main` → `506a60c`, `alerts-page-store-migration` → `e2e488b`,
  `arena/01a0ccea-socopilot` → `b9da463`.
- The five commits that carried `.soc_token` in the pre-second-purge history
  were: `a161257` (ancestor named in earlier ticket draft for
  `alerts-page-store-migration`), `2f23782` (cached head of `refs/pull/2`,
  titled "fix: security hardening — remove leaked JWT" — it removed
  `frontend/public/token.txt` while leaving the same secret as `.soc_token`),
  `14e6b4f`, `4e3b465`, `fa20c00`. All are now rewritten/pruned (commit count
  on `main` went 43 → 42, total across all branch refs 60 → 43, with one empty
  commit pruned).

What remains on GitHub's side is outside API reach, so we need your help
purging:

1. The cached pull-request head refs `refs/pull/1/head` … `refs/pull/8/head`
   for this repository. These still point at pre-second-purge commits that
   contain the removed blob and are still fetchable even though the
   corresponding PRs (#1–#8) are closed. Attempts to delete them via
   `git push --mirror` are rejected with `deny updating a hidden ref` on all
   eight, which is expected — only Support can clear them.
2. Any cached views/diffs/patches of the closed pull requests #1–#8
   (e.g. `github.com/gm-prog/socopilot/pull/2/files`) that may render content
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
- First purge: 2026-09-22 (`git filter-repo --invert-paths --path frontend/public/token.txt`) — incomplete, left `.soc_token`
- Second purge: 2026-09-23 (`git filter-repo --strip-blobs-with-ids`) — complete, by blob SHA
- Leaked blob SHA (same content at two paths): `b848f4c67b2635dcfd23b0107072eba560b7aeb4`
- Surviving path after first purge: `.soc_token` (same blob as `frontend/public/token.txt`)
- Additional blobs purged in second run (repomix outputs embedding the JWT):
  `37e1584a99e3e91989a4462842ff8b4eee95bb5d` (`frontend/repomix-output.xml`),
  `810cb38876477b74799de8b41970c077689aa86b` (`repomix-output.xml`),
  `bee9402d46abc32296fd645f84d1664bbbcdd137` (`repomix-output.xml`)
- Five commits carrying `.soc_token` before second purge: `a161257`, `2f23782`, `14e6b4f`, `4e3b465`, `fa20c00`
- Branch refs after second purge (force-pushed): `main` → `506a60c` (42 commits, verified 0 objects contain blob), `alerts-page-store-migration` → `e2e488b`, `arena/01a0ccea-socopilot` → `b9da463`
- Branch refs deleted in first purge: `master`, `devin/1780897696-add-unit-tests`, `devin/1780897699-improve-error-handling`, `devin/1780897707-refactor-shared-utilities`, `devin/1780897712-security-hardening`
- Closed PRs whose cached heads predate the second rewrite: #1, #2, #3, #4, #5, #6, #7, #8
- Cached head SHAs observed after second purge (still serving old history): `refs/pull/1` → `620c671`, `refs/pull/2` → `2f23782`, `refs/pull/3` → `785085a`, `refs/pull/4` → `68ff070`, `refs/pull/5` → `353faef`, `refs/pull/6` → `2897045`, `refs/pull/7` → `d45d538`, `refs/pull/8` → `ce68c90`
- Verification used: blob-SHA search (`git rev-list --objects origin/main | grep <sha>`), not path-based
