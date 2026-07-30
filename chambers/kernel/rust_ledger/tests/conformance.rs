use charge_ledger::{canonical_json, parse_json, Json, Ledger};
use std::fs;
use std::path::{Path, PathBuf};

fn corpus_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("ledger_traces")
}

fn obj_get<'a>(value: &'a Json, key: &str) -> &'a Json {
    match value {
        Json::Object(fields) => fields.get(key).unwrap(),
        _ => panic!("expected object"),
    }
}

fn case_names() -> Vec<String> {
    let mut names = Vec::new();
    for entry in fs::read_dir(corpus_dir()).unwrap() {
        let path = entry.unwrap().path();
        let file = path.file_name().unwrap().to_string_lossy();
        if let Some(name) = file.strip_suffix(".ledger.jsonl") {
            names.push(name.to_string());
        }
    }
    names.sort();
    names
}

#[test]
fn conformance() {
    let mut passed = Vec::new();
    for name in case_names() {
        let dir = corpus_dir();
        let ledger_text = fs::read_to_string(dir.join(format!("{name}.ledger.jsonl"))).unwrap();
        let expected_text = fs::read_to_string(dir.join(format!("{name}.expected.json"))).unwrap();
        let expected = parse_json(&expected_text).unwrap();
        let expected_fold = obj_get(&expected, "fold");
        let expected_audit = obj_get(&expected, "audit_codes");

        let ledger = Ledger::parse_jsonl(&ledger_text).unwrap();
        assert_eq!(
            ledger.to_canonical_jsonl(),
            ledger_text,
            "{name}: reserialize"
        );

        let fold = ledger.fold();
        assert_eq!(fold, *expected_fold, "{name}: fold structure");
        assert_eq!(
            canonical_json(&fold),
            canonical_json(expected_fold),
            "{name}: fold canonical string"
        );

        let audit = Json::Array(
            ledger
                .audit_codes()
                .into_iter()
                .map(Json::String)
                .collect::<Vec<_>>(),
        );
        assert_eq!(audit, *expected_audit, "{name}: audit_codes");
        passed.push(name);
    }
    eprintln!("conformance cases passed: {}", passed.join(", "));
    assert_eq!(passed.len(), 16);
}

#[test]
fn mutation_changes_verdict() {
    let dir = corpus_dir();
    let name = "honest-single-node";
    let ledger_text = fs::read_to_string(dir.join(format!("{name}.ledger.jsonl"))).unwrap();
    let expected_text = fs::read_to_string(dir.join(format!("{name}.expected.json"))).unwrap();
    let expected = parse_json(&expected_text).unwrap();
    let expected_fold = obj_get(&expected, "fold").clone();
    let expected_audit = obj_get(&expected, "audit_codes").clone();

    let mut mutated_lines = Vec::new();
    let mut changed = false;
    for line in ledger_text.lines() {
        if !changed && line.contains("\"debit_mbits\":73170") {
            mutated_lines.push(line.replacen("\"debit_mbits\":73170", "\"debit_mbits\":73171", 1));
            changed = true;
        } else {
            mutated_lines.push(line.to_string());
        }
    }
    assert!(changed, "mutation target not found");
    let mutated_text = format!("{}\n", mutated_lines.join("\n"));
    let mutated = Ledger::parse_jsonl(&mutated_text).unwrap();
    let mutated_fold = mutated.fold();
    let mutated_audit = Json::Array(
        mutated
            .audit_codes()
            .into_iter()
            .map(Json::String)
            .collect::<Vec<_>>(),
    );
    assert!(
        mutated_fold != expected_fold || mutated_audit != expected_audit,
        "numeric mutation should change the conformance verdict"
    );
}

#[test]
fn merge_is_idempotent() {
    let dir = corpus_dir();
    let text = fs::read_to_string(dir.join("honest-single-node.ledger.jsonl")).unwrap();
    let ledger = Ledger::parse_jsonl(&text).unwrap();
    let merged = ledger.merge(&ledger).unwrap();
    assert_eq!(merged.to_canonical_jsonl(), ledger.to_canonical_jsonl());
}
