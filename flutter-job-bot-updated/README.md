# Flutter freelance Telegram alerts (free-tier setup)

Daily at 09:00 IST (03:30 UTC), GitHub Actions runs `bot.py` and sends a Telegram digest. Scheduled workflows can run late or be disabled after repository inactivity. The laptop can be off.

## Filters
- Flutter in job title, explicit freelance/contract keywords
- Worldwide remote leads (reject obvious location restrictions; verify eligibility manually)
- Compatible with ~3.5 years experience when numeric requirements are stated; unspecified years accepted
- Reject explicit USD hourly rates entirely below $15; unspecified/fixed-price budgets accepted and **not verified**
- LinkedIn email alerts are **leads only**: email contents generally do not reliably reveal pay, experience or contract type. Verify the actual listing.
- Up to 20 new alerts per day; deduplication persisted to `sent_jobs.json` committed by workflow

## Setup
1. In Telegram open https://t.me/BotFather and create bot with `/newbot`. Send the bot `/start` and a message.
2. Visit `https://api.telegram.org/botYOUR_TOKEN/getUpdates` privately and find `message.chat.id`. Do not share your token.
3. Create a **public** GitHub repository, upload the contents of this folder (including `.github/workflows/daily.yml`). Never commit secrets.
4. In repository Settings → Secrets and variables → Actions add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
5. For LinkedIn: create Flutter freelance job email alerts on LinkedIn. Optional: configure Gmail IMAP and a Google app password (if eligible), then add `IMAP_USER` and `IMAP_APP_PASSWORD` secrets. Without these, the LinkedIn email source is skipped.
6. Repository Settings → Actions → General → Workflow permissions: allow Read and write permissions for history commits (if available).
7. Actions → Daily Flutter Job Alerts → Run workflow; inspect logs and Telegram.

## Cost / limitations
GitHub Free public repository Actions are normally free within GitHub's terms, subject to service policies. No purchases required for this personal use case. Public job feeds may rate-limit or change. LinkedIn offers no general free job-search API. Do not scrape LinkedIn. LinkedIn emails may be incomplete and email parsing can break when formats change. Job filtering is heuristic; no job feed can guarantee worldwide eligibility, freelance status, or compensation. Pay filtering recognizes explicit USD hourly formats; other currencies, monthly pay and fixed-price budgets need manual review. Job descriptions mentioning multiple experience ranges can lead to false positives. If a source fails, the bot logs a warning and continues.
