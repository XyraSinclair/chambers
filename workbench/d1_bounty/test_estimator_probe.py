"""The estimator-soundness lane as a standing test (ASSURANCE.md L3).

These assertions are the executable form of "an estimate you cannot attack is
not an estimate": if a future edit to egress.py's estimator ever undercharges a
modeled channel, `test_modeled_channels_are_sound` goes red. The unmodeled-
channel test PROTECTS the honest non-claim: it must stay a demonstrated leak,
so nobody quietly starts calling the accountant complete.
"""
from __future__ import annotations

from .estimator_probe import (
    probe_enum,
    probe_enum_amortized,
    probe_ordering,
    probe_text,
    probe_unmodeled,
    run_probe,
)


def test_modeled_channels_are_sound() -> None:
    # Every modeled channel: the secret is recovered exactly AND achieved bits
    # never exceed what the estimator charged. Soundness of the meter.
    report = run_probe(seeds=48)
    assert report.modeled, "probe produced no emissions"
    for r in report.modeled:
        assert r.recovered_exactly, f"{r.channel}({r.param}) did not decode"
        assert r.achieved_bits <= r.charged_bits + 1e-9, (
            f"UNDERCHARGE: {r.channel}({r.param}) carried {r.achieved_bits} bits "
            f"but was charged {r.charged_bits}"
        )
    assert report.all_modeled_sound
    # And the bound is TIGHT somewhere (achieved == charged on exact channels),
    # not merely safe by slack.
    assert report.worst_modeled_tightness >= 0.999


def test_amortized_adversary_stays_bounded() -> None:
    # The strong adversary (arithmetic coding across a run) approaches the
    # charged rate from below and never crosses it.
    for n in (3, 5, 6, 7, 10):
        r = probe_enum_amortized(n, symbols=60, seed=f"t/{n}")
        assert r.recovered_exactly
        assert r.achieved_bits <= r.charged_bits + 1e-9
        assert r.tightness >= 0.99  # genuinely tight over a long run


def test_exact_channels_are_exactly_tight() -> None:
    # Powers-of-two enums, and raw-byte text, are charged at exactly their
    # physical capacity — ratio 1.0, no slack.
    assert probe_enum(8, "x").tightness == 1.0
    assert probe_text(16, "x").tightness == 1.0


def test_unmodeled_channel_is_uncharged_capacity() -> None:
    # The honest limit, executable: real recoverable bits at zero charge.
    r = probe_unmodeled(16, "x")
    assert r.recovered_exactly
    assert r.charged_bits == 0.0
    assert r.achieved_bits > 0.0  # the leak the estimator cannot see


def test_probe_is_deterministic() -> None:
    a = run_probe(seeds=8)
    b = run_probe(seeds=8)
    assert [(r.channel, r.param, r.achieved_bits, r.charged_bits) for r in a.modeled] == \
           [(r.channel, r.param, r.achieved_bits, r.charged_bits) for r in b.modeled]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
