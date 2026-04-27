---
name: pr-code-review
description: Automated code review for pull requests using multiple specialized agents
---

Provide a code review for the given pull request and manage the full review lifecycle directly on the PR.

**Environment & Repository Access:**

- The full repository is already checked out locally. Use local file reads instead of fetching files remotely.
- The environment provides pull request metadata directly. Use PR number, base SHA, and head SHA. Do NOT rely on parsing PR URLs.

**Variable Resolution:**

- Replace `<base_sha>` with the provided base SHA value.
- Replace `<head_sha>` with the provided head SHA value.
- Never use the literal strings `<base_sha>` or `<head_sha>` in commands.

**Repository Identification:**

- Extract repository owner and name from the environment context.
- Do not attempt to infer from URLs.

**PR Context Retrieval:**

- Use provided environment metadata for PR number, base SHA, and head SHA.
- Use git and local repository to infer:
  - Changed files: `git diff --name-only <base_sha> <head_sha>`
  - Diff content: `git diff <base_sha> <head_sha>`
- Use GitHub integration tools only if additional metadata (title, body, existing comments) is required.

**Scope Constraint:**

- Only analyze code present in the git diff between base and head.
- Do NOT review unchanged files.

**GitHub Interaction Rules:**

- Use GitHub tools only for:
  - Posting comments
  - Updating PR description
  - Fetching PR metadata not available locally
- Do NOT use GitHub tools for reading code or diffs.

**Review History Retrieval:**

- Use GitHub integration tools to fetch:
  - Issue comments on the PR
  - Review comments on the PR
- Treat comments authored by the current automation identity as prior review feedback.

**CODING.md Resolution:**

- For each changed file:
  - Check the file's directory
  - Then walk up parent directories to root
  - Include the first CODING.md found in each path
- If no CODING.md exists anywhere, skip policy checks and note this in the final summary.

**Link Construction:**

- Use head SHA for all code references.
- Construct links using: `https://github.com/{owner}/{repo}/blob/{head_sha}/{file_path}#L{start}-L{end}`
- Provide at least 1 line of context before and after the flagged lines.

**Comment Discipline:**

- Do not post more than one comment per root cause.
- Prefer fewer, high-confidence comments over many low-confidence ones.

**Agent assumptions (applies to all review passes):**

- Assume tools are available, but if a tool lacks required context, fallback to local repository inspection instead of failing.
- Only call a tool if it is required to complete the task. Every tool call should have a clear purpose.
- If `--comment` is not provided, do not mutate GitHub state. Return findings only.
- Never include tool/agent/vendor names in PR comments, review comments, lifecycle messages, or PR description updates. Specifically avoid terms like `OpenCode`, `opencode`, and `Claude`.

Follow these steps precisely:

1. If `--comment` is provided, handle lifecycle comment as follows:

   - Fetch existing PR comments using this exact command:
      gh pr view {pr_number} --json comments

   - Do NOT use `gh api` to fetch comments
   - If fetching comments fails or is slow, skip fetching and create a new lifecycle comment instead
   - Search for a comment containing marker: `<!-- pr-review-lifecycle -->`

   - If such a comment exists:
     - Update that comment using GitHub API (PATCH issues/comments/{comment_id})
     - Use this exact command to update:
         gh api -X PATCH /repos/{owner}/{repo}/issues/comments/{comment_id} -f body="..."

   - If no such comment exists:
     - Create a new PR comment using GitHub integration tools with body:

       <!-- pr-review-lifecycle -->
       **Status**: In progress
       **Stage**: Started
       **Message**: review has started and context collection is running

   - If a legacy lifecycle comment exists with marker `<!-- opencode-pr-review-lifecycle -->`, update that same comment and replace its body with neutral wording.

2. Fetch PR context:
   - Determine changed files using: `git diff --name-only <base_sha> <head_sha>`
   - Fetch diff content using: `git diff <base_sha> <head_sha>`
   - Use GitHub integration tools to fetch: state, draft status, title, body, existing comments and reviews.

3. Stop only if one of these is true:
   - PR is closed
   - PR is draft
   - PR is clearly not reviewable (automated/version-bump/trivial change that is obviously safe)

   If stopping and `--comment` is provided, update lifecycle comment to:
   - Status: **Completed**
   - Stage: **Skipped**
   - Reason: explicit skip condition

4. Build a concise PR summary from title/body/diff (intent + major code areas + risk hotspots). Append or update this summary in the PR description using marker `<!-- pr-review-summary -->`. If marker exists, replace that block; if not, append it. If `--comment` is provided, update lifecycle comment stage to **Summary updated**.

5. Find relevant `CODING.md` files using the CODING.md Resolution rules above. Read them locally.

6. Fetch existing review feedback using the Review History Retrieval rules above. Do NOT early-stop because comments already exist.
   - Classify prior findings into: `resolved_by_new_code`, `still_open`, `unclear`
   - Use latest diff + current files to determine whether previously flagged issues were fixed
   - Never duplicate an existing still-open finding with another identical inline comment

7. Summarize the delta since the prior review: what changed since the last review cycle based on the diff.

8. Perform independent review passes — these must be logically independent and can be executed sequentially:

   Pass 1: `CODING.md` compliance
   Audit changes for compliance. When evaluating a file, only consider `CODING.md` files in that file's directory or parent directories (per CODING.md Resolution rules).

   Pass 2: `CODING.md` compliance (second independent pass)
   Same scope as Pass 1 but conducted independently to catch different violations.

   Pass 3: Bug detection (diff-only)
   Scan for obvious bugs in the diff only. Flag only significant bugs; ignore nitpicks and likely false positives. Do not flag issues that cannot be validated without context outside the diff.

   Pass 4: Security and logic issues
   Look for security vulnerabilities and incorrect logic within the changed code only.

   **CRITICAL: We only want HIGH SIGNAL issues.** Flag issues where:
   - The code will fail to compile or parse (syntax errors, type errors, missing imports, unresolved references)
   - The code will definitely produce wrong results regardless of inputs (clear logic errors)
   - Clear, unambiguous `CODING.md` violations where you can quote the exact rule being broken

   Do NOT flag:
   - Code style or quality concerns
   - Potential issues that depend on specific inputs or state
   - Subjective suggestions or improvements

   If you are not certain an issue is real, do not flag it. False positives erode trust and waste reviewer time.

   Each pass should be given the PR title and description for context.

   If `--comment` is provided, update lifecycle comment stage to **Analyzing code**.

9. Validate each issue individually. Only keep high-confidence issues. Discard uncertain findings. Preserve `severity` for kept issues.

   Severity rubric:
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
    - For each `new_validated_issue`, post one inline review comment using available GitHub integration tools
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

Do NOT flag these (false positives):

- Pre-existing issues
- Something that appears to be a bug but is actually correct
- Pedantic nitpicks that a senior engineer would not flag
- Issues that a linter will catch
- General code quality concerns unless explicitly required in `CODING.md`
- Issues mentioned in `CODING.md` but explicitly silenced in the code

Notes:

- Existing comments are inputs, not a stop condition. Always evaluate whether new commits fixed prior suggestions.
- If legacy bot comments contain vendor names, update those comments to neutral wording when permissions allow.
- Cite and link each issue in inline comments using the Link Construction rules above.
- For small, complete fixes, include a committable suggestion block. For larger changes, describe fix direction without a suggestion block.
- Never post a committable suggestion unless applying it fully resolves the issue.
- Only one comment per unique issue.