---
name: pr-code-review
description: Automated code review for pull requests using multiple specialized agents
allowed-tools: Bash(gh api:*), Bash(gh pr comment:*), Bash(gh pr diff:*), Bash(gh pr edit:*), Bash(gh pr review:*), Bash(gh pr view:*), Bash(gh pr list:*)
---

Provide a code review for the given pull request and manage the full review lifecycle directly on the PR using `gh` CLI.

**Agent assumptions (applies to all subagents):**

- All tools are functional and will work without error. Do not test tools or make exploratory calls. Make sure this is clear to every subagent that is launched.
- Only call a tool if it is required to complete the task. Every tool call should have a clear purpose.
- Parse the PR URL first and derive `{owner, repo, pr_number}` for all `gh` commands.
- If `--comment` is not provided, do not mutate GitHub state. Return findings only.
- Never include tool/agent/vendor names in PR comments, review comments, lifecycle messages, or PR description updates. Specifically avoid terms like `OpenCode`, `opencode`, and `Claude`.

To do this, follow these steps precisely:

1. If `--comment` is provided, create or update a lifecycle comment first (upsert by marker `<!-- pr-review-lifecycle -->`) with:
   - Status: **In progress**
   - Stage: **Started**
   - Message: review has started and context collection is running
   - If a legacy lifecycle comment exists with marker `<!-- opencode-pr-review-lifecycle -->`, update that same comment and replace its body with neutral wording.

2. Fetch PR context (`gh pr view`) including: state, draft, title, body, base ref, head ref, head SHA, files changed, and existing comments/reviews.

3. Stop only if one of these is true:
   - PR is closed
   - PR is draft
   - PR is clearly not reviewable (automated/version-bump/trivial change that is obviously safe)

   If stopping and `--comment` is provided, update lifecycle comment to:
   - Status: **Completed**
   - Stage: **Skipped**
   - Reason: explicit skip condition

4. Build a concise PR summary from title/body/diff (intent + major code areas + risk hotspots). Then append or update this summary in the PR description:
   - Use a marker block in PR body: `<!-- pr-review-summary -->`
   - If marker exists, replace that block; if not, append it
   - Do this early in the lifecycle so humans can see context immediately
   - If `--comment` is provided, update lifecycle comment stage to **Summary updated**

5. Launch a lightweight subagent to return a list of file paths (not contents) for relevant `CODING.md` files:
   - The root `CODING.md` file, if it exists
   - Any `CODING.md` files in directories containing files modified by the pull request

   If no `CODING.md` exists, continue review as bug-focused and report that policy checks were skipped due to missing `CODING.md`.

6. Fetch existing review feedback left by this reviewer identity (issue comments + review comments). Do NOT early-stop because comments already exist.
   - Classify prior findings into: `resolved_by_new_code`, `still_open`, `unclear`
   - Use latest diff + current files to determine whether previously flagged issues were fixed
   - Never duplicate an existing still-open finding with another identical inline comment

7. Launch a subagent to summarize the latest delta since prior review (what changed since the last review cycle).

8. Launch 4 subagents in parallel to independently review changes. Each returns issues with `description`, `reason` (e.g., `CODING.md adherence`, `bug`), and `severity`:

   Agents 1 + 2: `CODING.md` compliance subagents
   Audit changes for `CODING.md` compliance in parallel. When evaluating `CODING.md` compliance for a file, only consider `CODING.md` files in that file's directory or parent directories.

   Agent 3: Bug-finding subagent (parallel subagent with agent 4)
   Scan for obvious bugs. Focus only on the diff itself without reading extra context. Flag only significant bugs; ignore nitpicks and likely false positives. Do not flag issues that you cannot validate without looking at context outside of the git diff.

   Agent 4: Bug-finding subagent (parallel subagent with agent 3)
   Look for problems that exist in the introduced code. This could be security issues, incorrect logic, etc. Only look for issues that fall within the changed code.

   **CRITICAL: We only want HIGH SIGNAL issues.** Flag issues where:
   - The code will fail to compile or parse (syntax errors, type errors, missing imports, unresolved references)
   - The code will definitely produce wrong results regardless of inputs (clear logic errors)
   - Clear, unambiguous `CODING.md` violations where you can quote the exact rule being broken

   Do NOT flag:
   - Code style or quality concerns
   - Potential issues that depend on specific inputs or state
   - Subjective suggestions or improvements

   If you are not certain an issue is real, do not flag it. False positives erode trust and waste reviewer time.

   In addition to the above, each subagent should be told the PR title and description. This will help provide context regarding the author's intent.

   If `--comment` is provided, update lifecycle comment stage to **Analyzing code**.

9. For each issue from bug/policy subagents, launch parallel validation subagents. Keep only high-confidence validated issues and preserve `severity`.

Severity rubric (required for every validated issue):

- `critical`: exploitable security vulnerability, auth bypass, secret leakage, irreversible data loss/corruption, guaranteed production outage, or guaranteed runtime crash in common paths.
- `high`: definite logic/functional bug with significant user/business impact but not critical-level blast radius.
- `medium`: real issue with lower impact or narrower scope, still worth fixing.

If severity is uncertain between two levels, choose the lower level.

10. Merge results from steps 6 and 9:
   - `resolved_by_new_code` from prior cycle
   - `still_open` from prior cycle
   - `new_validated_issues` from current cycle
   - Remove duplicates by file + line + semantic root cause

11. If `--comment` is provided, update lifecycle comment stage to **Posting feedback**.

12. Post review output:
   - For each `new_validated_issue`, post one inline review comment (`gh pr review`/`gh api` as needed)
   - Prefix each inline comment with severity label in this exact format: `[severity: critical]`, `[severity: high]`, or `[severity: medium]`
   - Never post duplicate inline comments for the same still-open issue
   - Post one normal PR comment summary containing:
     - Fixed from previous review
     - Still open from previous review
     - New issues found in this cycle
     - Severity breakdown for new issues (critical/high/medium counts)
   - If no issues found, post:
     - "No issues found in this cycle. Checked for bugs and CODING.md compliance."
     - Include whether prior issues were resolved or still open

13. Final lifecycle update (`--comment` only):
   - Status: **Completed**
   - Stage: **Done**
   - Include counts: fixed prior issues, still-open prior issues, new issues, and severity breakdown

14. Error handling (`--comment` only): if any failure occurs after lifecycle comment creation, update lifecycle comment to:
   - Status: **Failed**
   - Stage: best-known stage
   - Message: concise failure reason

Use this list when evaluating issues (these are false positives, do NOT flag):

- Pre-existing issues
- Something that appears to be a bug but is actually correct
- Pedantic nitpicks that a senior engineer would not flag
- Issues that a linter will catch (do not run the linter to verify)
- General code quality concerns (e.g., lack of test coverage, general security issues) unless explicitly required in `CODING.md`
- Issues mentioned in `CODING.md` but explicitly silenced in the code (e.g., via a lint ignore comment)

Notes:

- Use gh CLI to interact with GitHub (e.g., fetch pull requests, create comments). Do not use web fetch.
- Create a todo list before starting.
- Existing comments are inputs, not a stop condition. Always evaluate whether new commits fixed prior suggestions.
- If legacy bot comments contain vendor names, prefer updating those comments to neutral wording when permissions allow.
- You must cite and link each issue in inline comments (e.g., if referring to `CODING.md`, include a link).
- For small, complete fixes, include a committable suggestion block. For larger changes, describe fix direction without suggestion block.
- Never post a committable suggestion unless applying it fully resolves the issue.
- Only one comment per unique issue.

- When linking to code in inline comments, follow the following format precisely, otherwise the Markdown preview won't render correctly: `https://github.com/OWNER/REPO/blob/FULL_SHA/path/to/file.py#L10-L15`
  - Requires full git sha
  - You must provide the full sha. Commands like `https://github.com/owner/repo/blob/$(git rev-parse HEAD)/foo/bar` will not work, since your comment will be directly rendered in Markdown.
  - Repo name must match the repo you're code reviewing
  - # sign after the file name
  - Line range format is L[start]-L[end]
  - Provide at least 1 line of context before and after, centered on the line you are commenting about (eg. if you are commenting about lines 5-6, you should link to `L4-7`)
