// Adversarial totality lane (2026-07-06). Born as the probe that convicted
// this port of reproducing the pre-fix spec's F1 bug verbatim (a forged
// null-payer escrow minted 999 into the conservation LHS with a clean
// audit: lhs=1999 rhs=1000, codes=[]). The corpus soups now pin exact
// byte-parity with the reference; THIS lane pins the two properties that
// must hold on ANY soup regardless of fixtures:
//   1. no panic on any total surface (parse, fold, audits, conservation);
//   2. the conservation identity telescopes (lhs == rhs).
use charge_ledger::{Ledger, SettlementVersion};

fn assert_total_and_conserved(name: &str, jsonl: &str) {
    let result = std::panic::catch_unwind(|| {
        let ledger = match Ledger::parse_jsonl(jsonl) {
            Ok(l) => l,
            Err(_) => return None, // rejected at the door: not a soup
        };
        let (lhs, rhs) = ledger.settlement_conservation_pair(SettlementVersion::V2);
        let _ = ledger.settlement_audit_codes();
        let _ = ledger.audit_codes();
        let _ = ledger.settlement_fold_v2();
        Some((lhs, rhs))
    });
    match result {
        Ok(Some((lhs, rhs))) => {
            assert_eq!(lhs, rhs, "{name}: conservation broke ({lhs} != {rhs})")
        }
        Ok(None) => {}
        Err(_) => panic!("{name}: PANIC — one-event denial-of-audit"),
    }
}

#[test]
fn adversarial_soups_are_total_and_conserved() {
    let cases: &[(&str, &str)] = &[
        (
            "F1 null-payer escrow mint",
            concat!(
                r#"{"account":"alice","amount_ucr":1000,"issuer":"bank","kind":"deposit","seq":1,"tick":0}"#, "\n",
                r#"{"amount_ucr":999,"charge_keys":[["exp","s","r"]],"default_on_expiry":"refund_to_payer","expires_tick":100,"issuer":"bank","kind":"escrow","payer":null,"payee":"bob","required_clean":true,"seq":2,"tick":1}"#, "\n",
            ),
        ),
        (
            "F2 reason_class object",
            "{\"kind\":\"charge\",\"reason_class\":{}}\n",
        ),
        (
            "F2 nested-list key lease",
            "{\"amount_mbits\":10,\"expires_tick\":9,\"issuer\":\"i\",\"key\":[[\"x\"]],\"kind\":\"lease\",\"lease_seq\":1,\"node\":\"n\"}\n",
        ),
        (
            "F2 list escrow_id release",
            "{\"amount_ucr\":5,\"charge_ids\":[\"sha256:0000000000000000000000000000000000000000000000000000000000000000\"],\"escrow_id\":[],\"issuer\":\"b\",\"kind\":\"release\",\"seq\":1,\"tick\":1}\n",
        ),
        (
            "F2 list attestation_id bond_resolution",
            "{\"amount_ucr\":5,\"attestation_id\":[],\"direction\":\"slash\",\"kind\":\"bond_resolution\",\"seq\":1,\"submitter\":\"x\",\"tick\":1}\n",
        ),
        (
            "I7 unparseable register key",
            "{\"ceiling_mbits\":50,\"issuer\":\"i\",\"key\":[[\"a\"]],\"kind\":\"register\",\"subject_entropy_mbits\":100}\n",
        ),
        (
            "non-string payee escrow + release",
            concat!(
                r#"{"account":"alice","amount_ucr":1000,"issuer":"bank","kind":"deposit","seq":1,"tick":0}"#, "\n",
                r#"{"amount_ucr":500,"charge_keys":[["exp","s","r"]],"default_on_expiry":"refund_to_payer","expires_tick":100,"issuer":"bank","kind":"escrow","payer":"alice","payee":7,"required_clean":false,"seq":2,"tick":1}"#, "\n",
            ),
        ),
    ];
    for (name, jsonl) in cases {
        assert_total_and_conserved(name, jsonl);
    }

    // The F1 conviction itself, asserted sharply: the null-payer escrow
    // must contribute NOTHING (1000 == 1000, never 1999) and must be
    // convicted S6 — the exact failure this lane was born from.
    let ledger = Ledger::parse_jsonl(cases[0].1).unwrap();
    let (lhs, rhs) = ledger.settlement_conservation_pair(SettlementVersion::V2);
    assert_eq!((lhs, rhs), (1000, 1000));
    assert!(
        ledger
            .settlement_audit_codes()
            .iter()
            .any(|c| c.starts_with("S6 ")),
        "the forged escrow must be convicted, not silently neutralized"
    );
}
