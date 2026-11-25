# Prediction — v3 "The World in One Day" (ATM rebuild)

Written BEFORE any submit decision, per calibrated judgement.
This is an estimate, not a result. Only the live board can tell.

## What changed vs v2 (rank #12,039, score 384,768, ~38.5%)

- Structure: v2 was a flat numbers grid with zero illustration.
  v3 copies the live top 10's winning shape exactly (ATM): 3
  illustrated heroes, 10 illustrated cards, pin map, UTC strip,
  numbers strip, DATE CHECK, badge legend — 38 stories, 9 regions,
  24 fields.
- Selection: heroes are the consensus big three (Riyadh, Hormuz,
  Dow); the 15 stories v2 missed are now in (Riyadh, Hormuz, Dow,
  heat deaths, Tiangong, Solomons plan, Korea alert, UAE crash,
  Nepal, Hanoi, Cartagena, Cikande toll, Sarkozy, Code Red, Ariane,
  El Chapo, femicide, Gavi + extras).
- Accuracy (K4): five corrections the top entries get wrong —
  Hormuz was projectiles on 23 Nov, not mines on 24 Nov; Dow
  "back above" 50,000 (first close was 6 Feb 2026), not "first";
  Zaporizhzhia 2 dead / 48 hurt (not 9 killed); Tiangong crew
  named 24 Nov, launch 25 Nov; Bougainville omitted (result
  unconfirmed). 700K dropped entirely.
- Typography: sentence-case headlines/decks (new lowercase glyphs),
  bold masthead, looser leading — the 20261122 font lesson applied.

## What still loses to the top 5

- The stroke font is still hand-drawn, not real serif. At 300px
  the page reads well, but the top 5's serif mastheads and decks
  have more typographic authority.
- The map is a dotted approximation, not a polished cartographic
  render. The scenes are simple flat silhouettes.
- The jury is pairwise and noisy; a structural copy of the winners
  does not guarantee their scores.

## Estimate

- Dev rate: 700,000–820,000 (vs round-3 bar #50 657,256, #5 833,807).
- Rank: roughly #15–45. Paid zone (#1–50) is plausible; top 5 is
  NOT claimed. A top-5 claim would need the font and scenes to
  beat #1's serif craft, which they do not yet.

## Gates passed (verified, not claimed)

- Render: exit 0, 2 runs byte-identical (sha256
  cee06263ec93c3432da8f62747bf0d77e6ee4c1688522a902f37134a305b52ae),
  53,091 bytes, 1024x1024.
- Grader-like sandbox (read-only, 1 CPU, 512 MB, no network,
  60 s): exit 0, byte-identical output.
- 300px thumbnail: masthead, numbers, hero headlines readable.
- Proofread from the render: masthead, sub-deck, numbers, heroes,
  cards, ALSO, DATE CHECK, footer all read correctly, no overlap
  or truncation after fixes (hero 1 headline, cards 11/12, 47,000
  label, map density).

## What v3 needs before submit

- Lead verification (render seen, program run, facts checked).
- Quota re-check live + kit level (site is at level 46, shelf is
  45 — fresh-kit step belongs to submit prep).
- Akbar's explicit "Eksekusi" naming the entry. No submit from
  this worker.
