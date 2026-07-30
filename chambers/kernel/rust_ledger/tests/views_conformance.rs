//! charge-views/1 conformance: the Rust port replays views_traces/
//! bit-for-bit from the input files alone, and reproduces the embedded
//! leakage_class/incident of EVERY frozen ledger fold under the
//! legacy-default policy (the VIEWS-SPEC §V.5 parity law, second
//! implementation).

use charge_ledger::{canonical_json, parse_json, views_report, Json};
use std::fs;
use std::path::{Path, PathBuf};

fn kernel_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf()
}

fn obj_get<'a>(value: &'a Json, key: &str) -> &'a Json {
    match value {
        Json::Object(fields) => fields.get(key).unwrap(),
        _ => panic!("expected object"),
    }
}

fn case_names(dir: &Path, suffix: &str) -> Vec<String> {
    let mut names = Vec::new();
    for entry in fs::read_dir(dir).unwrap() {
        let path = entry.unwrap().path();
        let file = path.file_name().unwrap().to_string_lossy();
        if let Some(name) = file.strip_suffix(suffix) {
            names.push(name.to_string());
        }
    }
    names.sort();
    names
}

#[test]
fn views_corpus_bit_for_bit() {
    let dir = kernel_dir().join("views_traces");
    let names = case_names(&dir, ".input.json");
    assert!(names.len() >= 6, "views corpus missing");
    for name in &names {
        let input_text = fs::read_to_string(dir.join(format!("{name}.input.json"))).unwrap();
        let expected_text = fs::read_to_string(dir.join(format!("{name}.expected.json"))).unwrap();
        let input = parse_json(&input_text).unwrap();
        let report = views_report(obj_get(&input, "fold"), obj_get(&input, "policy"));
        assert_eq!(
            canonical_json(&report) + "\n",
            expected_text,
            "{name}: report bytes"
        );
    }
    println!(
        "views conformance: {} traces matched bit-for-bit",
        names.len()
    );
}

#[test]
fn parity_law_over_frozen_ledger_folds() {
    // VIEWS-SPEC §V.5: under the legacy-default policy, the view's
    // class/incident equal the fold's embedded fields — checked against
    // the FROZEN corpus bytes, for every account of every trace.
    let default_policy = parse_json(
        r#"{"spec":"charge-views/1","name":"legacy-default","domains":null,
            "classes":[{"label":"negligible","max_permille":50},
                       {"label":"bounded","max_permille":250},
                       {"label":"material","max_permille":500},
                       {"label":"unsafe","max_permille":800}],
            "terminal_label":"reconstructed","incident_permille":800}"#,
    )
    .unwrap();
    let dir = kernel_dir().join("ledger_traces");
    let names = case_names(&dir, ".expected.json");
    assert!(names.len() >= 10, "ledger corpus missing");
    let mut checked = 0usize;
    for name in &names {
        let expected_text = fs::read_to_string(dir.join(format!("{name}.expected.json"))).unwrap();
        let expected = parse_json(&expected_text).unwrap();
        let fold = obj_get(&expected, "fold");
        let report = views_report(fold, &default_policy);
        let report_accounts = match obj_get(&report, "accounts") {
            Json::Array(rows) => rows,
            _ => panic!("{name}: view refused a frozen fold"),
        };
        let fold_accounts = match obj_get(fold, "accounts") {
            Json::Array(rows) => rows,
            _ => panic!("{name}: fold shape"),
        };
        assert_eq!(
            report_accounts.len(),
            fold_accounts.len(),
            "{name}: row count"
        );
        for (row, account) in report_accounts.iter().zip(fold_accounts.iter()) {
            assert_eq!(
                obj_get(row, "key"),
                obj_get(account, "key"),
                "{name}: order"
            );
            assert_eq!(
                obj_get(row, "class"),
                obj_get(account, "leakage_class"),
                "{name}: class parity"
            );
            assert_eq!(
                obj_get(row, "incident"),
                obj_get(account, "incident"),
                "{name}: incident parity"
            );
            checked += 1;
        }
    }
    assert!(checked > 0);
    println!(
        "parity law: {checked} accounts across {} frozen folds",
        names.len()
    );
}
