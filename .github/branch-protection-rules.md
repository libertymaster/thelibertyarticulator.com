# Recommended branch protection

Apply a ruleset to the default branch (`main`) after the repository and CODEOWNERS teams exist.

- Require pull requests; prohibit direct pushes and force pushes.
- Require two approvals and dismissal of stale approvals after new commits.
- Require review from code owners and resolution of every review conversation.
- Require signed commits where the organization can enforce them consistently.
- Require the `1 / lint`, `2 / security`, `3 / test`, and `4 / build and scan` checks to pass on the latest commit.
- Require the branch to be up to date or use a merge queue.
- Block merge when there are unresolved code-scanning or secret-scanning findings.
- Restrict bypass to a small emergency administrator group; log and review every bypass.
- Prevent branch deletion and creation of confusing matching refs.

Create a separate `production` environment for the deploy job:

- Require at least one operations reviewer who did not author the change.
- Restrict deployment to `main`.
- Store `DEPLOY_WEBHOOK_URL` and `DEPLOY_WEBHOOK_SECRET` as environment secrets.
- Store read-only `DHI_USERNAME` and `DHI_TOKEN` credentials as repository secrets
  for trusted main and tag image builds.
- Do not expose production secrets to pull-request jobs or untrusted forks.

Tags matching `v*` should be protected and created only from reviewed commits. The release job needs `contents: write`; other jobs use narrower permissions.

Reconcile these recommendations with organization policy and export the live ruleset to the security evidence repository. A Markdown file does not enforce protection by itself.
