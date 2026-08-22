# HP-SPGG Judge Prompt v1

Score the player's satisfaction in a sequential public-goods game as a scalar in `[0, 1]`.

Anchors:

- `0.0`: the outcome strongly violates the player's private behavioural profile.
- `0.5`: the outcome is mixed or only partially aligned with the player's profile.
- `1.0`: the outcome strongly aligns with the player's private behavioural profile.

Return only valid JSON with this schema:

```json
{"score": 0.0}
```
# HP-SPGG Judge Prompt v1

Return only a JSON object with key `score`, where `score` is a scalar from 0.0 to 1.0.

Anchors:

- `0.0`: the persona is clearly unsatisfied by the action and public-good outcome.
- `0.5`: the persona has mixed satisfaction.
- `1.0`: the persona is strongly satisfied by both the action and public-good outcome.

Apply the persona's private goal, the chosen contribution, and the group mean contribution. Do not reward verbosity or rhetoric; score the outcome.
