---
name: mm-file
description: File credit-card statements into Money Manager (self-hosted) with minimal tokens. Use when the user says "file expenses", "update MM", "upload statements to money manager", or mentions credit-card statement filing. Main thread orchestrates; one mm-filer subagent per statement executes.
---
<!-- Public copy. Personal paths, names and ids are replaced with placeholders. -->

# MM expense filing — token-lean pipeline

## Architecture (why this exists)
The old flow (cowork money-manager skill) drove the MM browser tab via Claude-in-Chrome and
read PDFs + XML dumps in one chat — it burned a whole session limit. This pipeline replaces it:

- **Main thread (any model): orchestrate only.** Never open a PDF, never read MM XML, never
  drive a browser. ~200 tokens per statement.
- **`scripts/mm_api.py`: zero-model HTTP client.** Talks to the MM server directly over LAN
  (probe/get/add/transfer/balance/verify). No browser needed — this machine reaches the LAN address.
- **`mm-filer` agent (Sonnet), one per statement:** reads the local synced PDF (or downloads it
  by fileId when given one) into its own throwaway context, extracts text locally with
  pypdf, files rows via mm_api.py, verifies TAD,
  returns a ≤10-line receipt.

## Orchestration recipe (main thread)
1. `python3 ~/.claude/skills/mm-file/scripts/mm_api.py probe` — MM URL changes on every server
   restart; if probe fails, ask the user to start MM / give the current `<server-ip:port>`.
2. List new statements — LOCAL FIRST (a sync client mirrors them):
   `<synced-statements-folder>/`
   one subfolder per bank; pattern `YYYY_MM <Card>.pdf`.
   Fallback cloud connector folder ids: the parent `<folder-id>`, plus one per bank.
   ⚠️ **Check the sync client is running first** (`pgrep -f "<sync-client>"`). If it is quit, the
   local folder looks merely *out of date* rather than broken — recent months are simply absent
   from `ls`, and reading an unmaterialized file hangs for minutes then dies with `TimeoutError:
   [Errno 60]`. Do not conclude "no statements exist" from the local listing; confirm in the
   cloud copy (`search_files` on `title contains 'YYYY_MM'`) and dispatch filers with fileIds.
   Skip any statement that cannot be opened yet.
3. For each statement not yet filed: dispatch one `mm-filer` agent at a time with
   local PDF path (or cloud fileId as fallback), card key, statement month.
4. Collect receipts, report one summary table to the user.

## Golden rules (distilled bug history — filer agents MUST read and obey)
A card in MM is a **running ledger, not a per-cycle worksheet**:
`Balance = Σ(purchases as Expense) − Σ(refunds/credits as Income) − Σ(bill payments as Transfer-in)`
The statement Total Amount Due (TAD) emerges naturally — **never force a cycle's net to equal TAD**.

- **Round-off test:** user's own round-offs are always ≤ ₹1. Needing an adjustment > ₹1 means a
  real missing/duplicated transaction (refund, cashback, EMI interest double-count, mis-recorded
  payment). Find it; never paper over it.
- Entry types: purchase/fee/interest/GST = **Expense** (inOutCode 1); refund/cashback/waiver/
  product return = **Income** (inOutCode 0, category Refund mcid `<category-id>`, Cashback mcid
  `<category-id>`); bill payment = **Transfer-in** `<payment-account>` → card
  (inOutCode 3, note "Payment").
- **Returns are credits, not expenses.** Booking a return as expense double-counts.
- **Every paid bill needs its payment transfer** — most-missed step. Amount/date come from the
  next statement's payment-received line (= previous TAD).
- Transfers go through `mm_api.py transfer` (endpoint `/moneyBook/moveAsset`).
  `/moneyBook/create` silently corrupts transfers — never use it for payments.
- **EMI traps:** a prefix such as "EMI" or "Pay in EMIs" on a merchant line = eligibility only, book full value. A real
  installment line (printed with an installment counter such as xx/xx) already includes interest — never add a
  separate interest line. Installments shrink month-to-month — always copy the printed amount,
  never reuse last month's. EMI conversion shows a reversing EMI-conversion credit; the
  statement's Purchases figure is already net.
- Overpayment = book the real (larger) payment transfer, never extra income.
- **Match the printed TAD exactly** — never infer from previous-balance/outstanding, never assume
  bank rounding (some banks round to rupees, others print paise).
- **Legit MM-above-TAD gaps — don't "fix":** a charge that posts after the statement closes can
  legitimately sit above the printed amount due. The general mechanism: a
  recurring charge is recorded in MM on its transaction date but the bank bills it a cycle late,
  so it sits *inside* the cycle window yet is absent from the printed statement. Confirm by
  checking that the statement's own Purchases figure sums without it, then leave it alone.
  A bill that is not yet paid also shows as a gap and is also correct; never book a payment that
  hasn't happened. Neither gap is closed with a balancing entry.
- **An app-store merchant descriptor = any app-store purchase**, not a particular product. The
  merchant string tells you nothing about what was bought — ask the user before
  categorizing. A large app-store charge can be an annual plan that replaces earlier monthly
  charges of the same service; once it lands, do not expect the monthly ones to recur.
- Categories: copy the mcid a similar past row of the same merchant used
  (`mm_api.py get 2026-01-01 2026-12-31 --asset <card>` and grep the merchant).

## Server quirks
- **The "server" is the user's phone** (discovered 2026-07-17): the Money Manager iOS app's
  PC Manager feature. iOS suspends the app on backgrounding/screen-lock — the HTTP listener dies.
  That's what looks like "crashes". Operating procedure: before any filing burst, ask the user to
  keep the MM app FOREGROUND with screen awake until told done; URL (ip AND port) changes on
  every app reopen / network switch — always `probe`; do all server work in short bursts
  (extract/plan offline first, then touch the server for the minimum window).
- Be gentle anyway: one dedupe `get` per statement, `--payname` from that output (never per-add
  ledger lookups), script paces writes 0.5s, ≤2 balance/verify calls per card, never run filer
  agents in parallel. Connection refused/reset mid-batch = app suspended — stop everything, ask
  user to reopen MM, `probe`, re-dedupe before re-adding (interrupted writes may have landed).
- `mbCash=0` ignored on update — use 0.01 instead.
- **`/moneyBook/update` and `/moneyBook/delete` are REAL** (verified 2026-08-22 against the UI's
  own `moneybook.js`; the old "delete API is fake, UI only" note was wrong). The ExtJS grid posts:
  - **update** → `moneyBook/update` with the row's *full* field set (`id`, `mbDate`, `mbCash`,
    `mbContent`, `mbDetailContent`, `inOutCode`, `inOutType`, `payType`, `assetId`, `mcid`,
    `mcscid`, `mbid`) — fetch current values via `getDataByPeriod` first and resend all of them,
    changing only what you mean to change. Returns `{success:true}`.
  - **delete** → `moneyBook/delete` with `ids=:id1:id2` (leading colon, colon-separated).
  Use `mm_api.py raw` so spaces encode as `%20` (the server does not decode `+`). After any
  update, re-download the sqlite and confirm live row count AND card balance are unchanged —
  that is what proves you edited a row rather than spawning a duplicate.
- Writes sometimes hang but land — always verify with `get` before retrying.
- **Calibration (first live run only):** the exact POST field names for `/moneyBook/create` are
  unverified from HTTP (old flow used the browser). File ONE test expense, `get` it back; if
  fields are off, inspect a real row's XML and adjust `mm_api.py add` params, then proceed.
  Same for `transfer` — verify with `get`, confirm inOutCode 3 + correct toAssetId.

## Card keys (mm_api.py) / cycles
Each card has a key in mm_api.py and a statement cycle (start day to end day), kept in the private script. Payment source: `<payment-account>`.

## Verify every time — via DB download, NEVER via HTTP row-sums
`mm_api.py verify`/`balance` over HTTP is BROKEN (transfer serialization mismatch — gave false
FAILs incl. a phantom large negative gap on one card; DB-level recompute showed every card 0.00 off).
Correct method (1 server call, rest offline):
1. `curl -s -m 8 -o /tmp/mm_live.sqlite http://<server-ip:port>/moneyBook/money.sqlite`
2. `python3 ~/.claude/skills/mm-file/scripts/verify_db.py /tmp/mm_live.sqlite <card-uuid> <TAD> [--until YYYY-MM-DD]`
Must PASS ≤ ₹1. Use `--until <cycle-close-date>` for cards carrying future-dated EMI rows.
Legit non-zero cases (verify_db.py prints CHECK; confirm by hand): balance = TAD − already-booked
payment (already paid) or TAD + post-close purchase (post-close charge).
- **No category CRUD over HTTP** (verified 2026-08-22 against all PC Manager JS + root HTML). The
  complete write surface is `moneyBook/create`, `/update`, `/delete`, `/moveAsset`,
  `/uploadSqlFile`. Categories load client-side into an empty `JsonStore`; nothing touches
  `ZCATEGORY`. To add a category/subcategory the user must do it in the iOS app — ask, then
  assign via `/moneyBook/update`. Do NOT reach for `uploadSqlFile`: it replaces the whole DB
  (clobbers concurrent phone edits) and hand-inserted rows lack the app's per-row sync state.
- **Categories are two-level:** row carries `mcid` (category) + `mcscid` (subcategory). Read the
  full tree offline from the sqlite `ZCATEGORY` table (`ZUID`=id, `ZPUID`=parent, filter
  `ZISDEL`); the HTTP row XML also returns display names as `mbCategory` / `subCategory`.
  ⚠️ Names are user-renamed defaults — `<id-a>` reads "Family" but is the old "Beauty" tree, and
  "Other" exists twice (`<id-b>` and `<id-c>`). Always copy the id a comparable past row used, never
  match on name.
