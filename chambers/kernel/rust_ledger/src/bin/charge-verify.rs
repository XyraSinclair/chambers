//! charge-verify — the stranger's one-command receipt verifier (Rust twin).
//!
//!     charge-verify <receipt.jsonl>
//!
//! Recomputes the charge-ledger/1 information fold, the charge-settlement
//! value fold, audit verdicts, and conservation identity from the artifact
//! alone, using the independent from-spec implementation. Exit codes:
//!
//!     0   clean (no audit findings)
//!     1   findings (printed; the receipt convicts itself)
//!     2   unreadable artifact / usage error
//!
use std::process::ExitCode;

use charge_ledger::{canonical_json, identity_codes, Ledger};

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 2 {
        eprintln!("usage: charge-verify <receipt.jsonl>");
        return ExitCode::from(2);
    }
    let text = match std::fs::read_to_string(&args[1]) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("UNREADABLE: {e}");
            return ExitCode::from(2);
        }
    };
    let ledger = match Ledger::parse_jsonl(&text) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("UNREADABLE: {e:?}");
            return ExitCode::from(2);
        }
    };

    // Reserialization check: a conforming artifact round-trips byte-for-byte.
    let reserialized = ledger.to_canonical_jsonl();
    if reserialized != text {
        println!("note: artifact was not in canonical form; verifying the canonicalized set");
    }

    println!("information_fold: {}", canonical_json(&ledger.fold()));

    let settlement_version = ledger.inferred_settlement_version();
    println!("settlement_spec: {}", settlement_version.spec_name());
    println!(
        "settlement_fold: {}",
        canonical_json(&ledger.settlement_fold_for_version(settlement_version))
    );
    let (conserved, deposited) = ledger.settlement_conservation_pair(settlement_version);
    println!("conservation: [{conserved},{deposited}]");

    let i_codes = ledger.audit_codes();
    let s_codes = ledger.settlement_audit_codes();
    let a_codes = identity_codes(&ledger);
    let conservation_ok = conserved == deposited;

    if i_codes.is_empty() && s_codes.is_empty() && a_codes.is_empty() && conservation_ok {
        println!("CLEAN: no charge-ledger/1, settlement, or identity findings");
        ExitCode::from(0)
    } else {
        if !i_codes.is_empty() {
            println!("information findings:");
            for c in &i_codes {
                println!("  {c}");
            }
        }
        if !s_codes.is_empty() {
            println!("settlement findings:");
            for c in &s_codes {
                println!("  {c}");
            }
        }
        if !a_codes.is_empty() {
            println!("identity findings:");
            for c in &a_codes {
                println!("  {c}");
            }
        }
        if !conservation_ok {
            println!("CONSERVATION BROKEN: [{conserved},{deposited}]");
        }
        println!(
            "CONVICTED: {} finding(s)",
            i_codes.len() + s_codes.len() + a_codes.len() + usize::from(!conservation_ok)
        );
        ExitCode::from(1)
    }
}
