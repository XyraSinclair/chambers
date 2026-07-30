//! Data-driven conformance: every golden trace in ../traces must agree
//! bit-for-bit with this independent implementation. One failing field in one
//! charge of one trace fails the suite, naming trace + index + field.

use std::fs;
use std::path::{Path, PathBuf};

use egress_accountant::{diff_decision, load_trace, replay};

fn trace_files() -> Vec<PathBuf> {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("..").join("traces");
    let mut v: Vec<PathBuf> = fs::read_dir(dir)
        .expect("traces dir")
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.extension().map(|x| x == "json").unwrap_or(false))
        .filter(|p| p.file_name().map(|n| n != "MANIFEST.json").unwrap_or(false))
        .collect();
    v.sort();
    v
}

#[test]
fn all_traces_agree_bit_for_bit() {
    let files = trace_files();
    assert!(files.len() >= 7, "expected the full corpus, found {}", files.len());

    let mut failures = Vec::new();
    let mut n_decisions = 0;
    for path in &files {
        let trace = load_trace(&fs::read_to_string(path).unwrap());
        let actual = replay(&trace);
        assert_eq!(
            actual.len(),
            trace.expected.len(),
            "{}: decision count mismatch",
            trace.name
        );
        for (i, (a, e)) in actual.iter().zip(trace.expected.iter()).enumerate() {
            n_decisions += 1;
            if let Some(field) = diff_decision(a, e) {
                failures.push(format!("{}[{}].{}: rust={}", trace.name, i, field, a.to_json()));
            }
        }
    }

    assert!(
        failures.is_empty(),
        "{} conformance divergences:\n{}",
        failures.len(),
        failures.join("\n")
    );
    eprintln!(
        "conformance OK: {} traces, {} decisions agree bit-for-bit",
        files.len(),
        n_decisions
    );
}
