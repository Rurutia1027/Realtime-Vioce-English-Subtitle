# Design: ASR Quality Booster for Pronunciation Practice

## Goal

Improve recognition quality and subtitle readability without sacrificing realtime experience or causing OOM regressions.

## Context

Current app is a lightweight live subtitle overlay. Main pain points:

- fragmented/short sentence outputs
- occasional wrong words for non-native pronunciation
- noisy environments
- quality-latency trade-off

## Feature Set

### 1) Text post-processing pipeline

Add a deterministic cleanup stage after ASR:

- collapse repeated spaces
- remove repeated adjacent tokens (`the the` -> `the`)
- optional punctuation assist for subtitle readability
- custom replacement dictionary (`hte` -> `the`, user-defined patterns)

Output remains one subtitle line.

### 2) Model profile switch

Expose model profiles:

- `fast`: `tiny.en` (lowest latency)
- `balanced`: `base.en`
- `accurate`: `small.en` (higher CPU/RAM)

Allow startup selection:

```bash
python3 live_caption_overlay.py --profile balanced
```

### 3) Confidence-aware display

If backend provides segment confidence/logprob:

- highlight low-confidence output with prefix `~`
- optional color tint for uncertain text

If unavailable, skip gracefully.

### 4) Stability and OOM guardrails

Build on existing protections:

- bounded queues
- error throttling
- single worker in fallback path

Add:

- memory watermark watchdog (soft warning)
- optional auto-reinit ASR backend after repeated failure bursts

### 5) Audio input precheck

Before live loop:

- detect default input device
- show sample rate / channels
- warn if clipping or silence-dominant signal

This helps fast troubleshooting when using headset mics.

## Architecture Changes

1. `ASR output`
2. `Quality middleware` (new module)
3. `Confidence annotator` (optional)
4. `Renderer`

New module proposal:

- `text_quality.py`
  - `normalize_text()`
  - `dedup_tokens()`
  - `apply_replacements()`
  - `format_subtitle()`

## Config Proposal

```env
ASR_PROFILE=balanced
POSTPROCESS_ENABLED=true
REPLACEMENT_DICT_PATH=./replacements.json
CONFIDENCE_HINT=true
ENABLE_MEMORY_WATCHDOG=true
```

## Incremental Rollout

### Phase 1 (quick win)

- text cleanup
- model profile selection
- replacement dictionary

### Phase 2

- confidence hints
- audio precheck

### Phase 3

- watchdog + backend auto-reinit
- telemetry summary for tuning

## Testing Plan

- 10-min, 30-min, 60-min soak tests
- profile benchmark:
  - latency
  - WER proxy (manual sampled checks)
  - memory footprint
- headset vs laptop mic A/B test
- non-native accent script regression set

## Success Metrics

- fewer fragmented lines per minute
- lower manual correction rate during recording
- no OOM in 60-minute continuous run
- stable subtitle latency under chosen profile

