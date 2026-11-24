# AI Office Assistant – Demo (n8n)

> **Own project / demo, not client work.**
> Sanitized copy of a privately operated n8n system (1 main workflow, 11 tool workflows). All test data is synthetic. The workflows in this repository are **inactive** and were **not run against real services** in this demo.
> Deutsche Fassung: [README.md](README.md)

## What the system does

You send the assistant a request in plain language via Telegram, for example: "Find the latest email from Ms Muster and prepare a reply with the contract." An AI agent (OpenAI) picks tools for it:

| Area | Tools | Approval needed? |
|---|---|---|
| Read Gmail | search emails, read an email, read an attachment (DOCX, PDF) | no (read-only) |
| Gmail drafts | reply draft, new draft with one attachment from Google Drive | no – a draft is not sent |
| Send Gmail | send a draft | **yes** |
| Google Drive | search files, read a document | no (read-only) |
| Google Calendar | read events, check availability | no (read-only) |
| Google Calendar | create, update, delete an event | **yes** |

**Approval:** before an email is sent and before any calendar change, the system sends an approval message in Telegram ("✅ E-Mail senden" / "❌ Abbrechen"). Without a yes, none of this happens. [`scripts/validate.py`](scripts/validate.py) checks automatically that every writing tool is attached to the agent only through an approval node (S11).

**Sender filter:** only the configured Telegram user ID is served; all other messages are silently ignored (S12, logic test F1–F5).

**Language:** the assistant answers in the language of the message, German or English. Approval messages and tool messages are in German.

Flow and all nodes: [docs/architecture.md](docs/architecture.md) (German).

## Contents

| Path | Contents |
|---|---|
| [`workflows/ki-bueroassistent.json`](workflows/ki-bueroassistent.json) | main workflow "KI-Büroassistent (Demo)" (26 nodes) |
| [`workflows/tools/`](workflows/tools/) | 11 tool workflows (85 nodes) |
| [`docs/`](docs/) | setup, architecture, test plan, privacy (German) |
| [`test-data/`](test-data/) | synthetic test messages and test data |
| [`tests/logic-harness/`](tests/logic-harness/) | repeatable logic test (10 scenarios, isolated n8n, Docker) |
| [`evidence/`](evidence/) | validation report, import test, logic test, live-test log |
| [`scripts/`](scripts/) | sanitizing (`sanitize.py`) and checking (`validate.py`) |
| [`SECURITY.md`](SECURITY.md) | what was removed, risks, reporting problems (German) |

## Import in brief

1. Import all 12 files – easiest via CLI: `n8n import:workflow --separate --input=<folder>`. The demo IDs are kept and the 11 tools are connected to the main workflow right away. When importing through the UI, re-select the tools in the main workflow ([setup](docs/setup.md)).
2. Connect credentials: Telegram, Gmail, Google Drive, Google Calendar (OAuth2), OpenAI.
3. Enter **your Telegram user ID** in `IF — Allowed Sender?` (placeholder `REPLACE_WITH_TELEGRAM_USER_ID`); without it the assistant answers nobody.
4. Create the data table `AI_DRAFT_REGISTRY` and select it in the tool "Gmail Create Draft — Single Attachment" (placeholder `REPLACE_WITH_DATA_TABLE_ID`).
5. Replace `[Your Name]` in the system message with your own name (closing of drafts).
6. Test only with **test accounts** and your own bot.

## Status & limits

### Checks (24 Nov 2026)

| Area | Status | Evidence |
|---|---|---|
| Sanitizing: allowed keys, pattern scan of all files, structure, workflows = output of `sanitize.py` | PASS per automatic report (valid only for the file state at that time) | [`evidence/validation-report.txt`](evidence/validation-report.txt) |
| Approval before sending and calendar changes; sender filter right after the trigger (static checks S11, S12) | PASS; seven deliberately altered copies were all detected | [`evidence/validation-notes.md`](evidence/validation-notes.md) |
| Local import of all 12 workflows into n8n 2.43.7 (isolated, no network) | PASS: IDs, parameters and connections unchanged, 11 of 11 tool references resolved | [`evidence/import-test.md`](evidence/import-test.md) |
| Logic test with sample data (sender filter, delete event, Gmail search) | PASS, 10 of 10; **not** Google, Telegram or the model | [`evidence/logic-test.md`](evidence/logic-test.md) |
| Live tests in the author's private system (previous version in Russian, without sender filter) | DOCUMENTED, partial; no public evidence | [`evidence/live-test.md`](evidence/live-test.md) |
| This version (German/English, with sender filter) with real services | NOT TESTED | [`docs/test-plan.md`](docs/test-plan.md) |

> **Local import ≠ functional test of the integrations.**

### Known limits

**E1 – approval shows only IDs.** The approval message for sending names only the draft ID, the one for deleting only the event ID – not recipient, subject or event title. Whoever approves should look at the draft or event first (after creating a draft the assistant reports recipient, subject and attachment). For create and update, the approval shows the parameters of the tool call.

**E2 – untrusted text in the prompt (prompt injection).** Emails, attachments and documents are untrusted. The system message forbids following instructions found in them; this is not guaranteed. Read tools and drafts run without approval; sending and calendar changes do not (see [SECURITY.md](SECURITY.md)).

**E3 – approval via link.** In n8n 2.43.7 the buttons directly in the Telegram chat did not react in the private system; there, approval is confirmed via a link. In the export, chat approval is switched on for "APPROVAL — Calendar Create" but not for the other three; which variant works in another instance was not tested.

**E4 – sender filter is new.** It was added on 24 Nov 2026 after it turned out that, by configuration, anyone who found the bot could give requests and receive the approvals themselves (approval goes to the sender of the message). In the logic test it rejects foreign and missing senders; rejecting a foreign account was not tested live.

**E5 – data sent to OpenAI.** Content of read emails (up to 6000 characters), attachments (up to 8000 characters), read documents, events and the conversation go to the model ([privacy](docs/datenschutz.md)).

**E6 – language.** This version answers in German or English. The privately tested version answered in Russian; the German/English version has not been tested live.

**E7 – tool scope.** One attachment per draft; reading attachments: DOCX and PDF; reading documents: PDF and Google Docs (via PDF), no sheets or slides. Time zone fixed to `Europe/Zurich`. The "AVAILABLE TOOLS" list in the system message does not name all connected tools; small typos in the message were kept unchanged.

**E8 – duplicate drafts.** The "draft with attachment" tool records created drafts in the n8n data table `AI_DRAFT_REGISTRY`; it does not run without that table. The reply draft has no such protection.

**E9 – errors and memory.** If a service fails, the assistant reports it as far as the tool returns a result; an error in the main workflow leads to no reply. The conversation memory (window per chat) is not cleared.

### Not tested

- Running this version with real services; activation, connecting credentials, webhook.
- Model behaviour under targeted prompt injection.
- n8n versions other than 2.43.7 and the `linux/amd64` platform.

## Privacy

The system processes emails, documents and events and sends parts of them to providers outside Switzerland (OpenAI, Google, Telegram): [docs/datenschutz.md](docs/datenschutz.md) (German). No legal advice, no compliance claim.

## Licence

MIT – see [LICENSE](LICENSE). Own development, created with the help of AI assistants.
