# Design: Realtime Translation for Live Caption Overlay

## Goal

Add low-latency realtime translation on top of current live English captions, while keeping the UI stable for recording workflows.

## Scope

- Input: microphone speech (mainly English)
- Existing output: single-line subtitle text
- New output: translated subtitle (optional dual-line mode)
- Keep local-first architecture when possible

## Non-Goals

- Full conversational AI
- Multi-speaker diarization
- Cloud-only dependency as a hard requirement

## User Stories

- As a speaker, I can see translated text while speaking.
- As a creator, I can switch between `EN only` and `EN + translation` display.
- As a user with weak network, I can still run with local translation.

## Architecture

1. `Audio capture + ASR` (existing)
2. `Text normalization` (new shared middleware)
3. `Translation worker` (new)
4. `Subtitle renderer` (update UI mode)

### Data Flow

1. ASR emits text segment
2. Normalize text (trim, dedup spaces, optional punctuation fix)
3. Push normalized text into translation queue
4. Translation worker pulls latest item (drop stale backlog)
5. Renderer updates subtitle line(s)

## Translation Backends

### Option A: Local translation (default)

- Candidate: `Helsinki-NLP/opus-mt-en-zh` via `transformers`
- Pros: no API fee, no token billing, private/local
- Cons: first-run model download, CPU load

### Option B: Cloud translation (optional adapter)

- Candidate: DeepL / Google / OpenAI translation endpoint
- Pros: better quality for some domains
- Cons: paid, network dependency

## UI Modes

- `single`: translated line only
- `dual`: line 1 original, line 2 translated
- `original`: keep current behavior

Runtime toggle examples:

- keyboard: `Cmd+1`, `Cmd+2`, `Cmd+3`
- config flag: `DISPLAY_MODE=dual`

## Performance Budget

- ASR-to-display latency target: < 1.2s (single sentence chunk)
- Translation extra latency target: < 350ms median (local small model)
- Queue max size: 3 (already in place pattern)

## Reliability Strategy

- Translation queue uses "latest-wins" policy.
- On translator error:
  - show original text
  - log throttled warning
  - retry with backoff

## Configuration Proposal

```env
ENABLE_TRANSLATION=true
TARGET_LANG=zh
DISPLAY_MODE=dual
TRANSLATION_BACKEND=local
```

## Implementation Plan

1. Add `translator.py` abstraction:
   - `translate(text) -> str`
2. Add translation worker thread and bounded queue.
3. Add display mode switch in overlay renderer.
4. Add config loader (`.env` or constants).
5. Add fallback behavior and error throttle.

## Testing Plan

- Unit:
  - normalization behavior
  - queue overflow behavior
  - backend fallback behavior
- Manual:
  - noisy room test
  - long sentence test
  - network-off test (local backend)
  - 30-minute memory stability run

## Risks and Mitigations

- Risk: CPU spike from ASR + translation
  - Mitigation: smaller translation model, worker throttling
- Risk: translation lag
  - Mitigation: latest-wins queue and shorter chunks
- Risk: unstable first-run download
  - Mitigation: startup preflight model check

