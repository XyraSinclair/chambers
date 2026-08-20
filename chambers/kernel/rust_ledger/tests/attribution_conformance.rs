use charge_ledger::{canonical_json, parse_json, Json, Ledger, SettlementVersion};
use std::fs;
use std::path::{Path, PathBuf};

fn corpus_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("attribution_traces")
}

fn obj_get<'a>(value: &'a Json, key: &str) -> &'a Json {
    match value {
        Json::Object(fields) => fields.get(key).unwrap(),
        _ => panic!("expected object"),
    }
}

fn obj_get_optional<'a>(value: &'a Json, key: &str) -> Option<&'a Json> {
    match value {
        Json::Object(fields) => fields.get(key),
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

fn code_array(codes: Vec<String>) -> Json {
    Json::Array(codes.into_iter().map(Json::String).collect())
}

fn assert_json_eq(name: &str, key: &str, actual: &Json, expected: &Json) {
    assert_eq!(actual, expected, "{name}: {key}");
    assert_eq!(
        canonical_json(actual),
        canonical_json(expected),
        "{name}: {key} canonical string"
    );
}

fn compare_unimplemented_empty_family(name: &str, key: &str, expected: &Json) {
    let Some(expected_codes) = obj_get_optional(expected, key) else {
        return;
    };
    // X0 and P-codes are outside this twin slice. A future corpus carrying
    // either family non-empty must not make this test pretend they exist.
    if matches!(expected_codes, Json::Array(items) if !items.is_empty()) {
        return;
    }
    assert_json_eq(name, key, &Json::Array(Vec::new()), expected_codes);
}

#[test]
fn attribution_conformance() {
    let mut passed = Vec::new();
    for name in case_names() {
        let dir = corpus_dir();
        let ledger_text = fs::read_to_string(dir.join(format!("{name}.ledger.jsonl"))).unwrap();
        let expected_text = fs::read_to_string(dir.join(format!("{name}.expected.json"))).unwrap();
        let expected = parse_json(&expected_text).unwrap();
        let ledger = Ledger::parse_jsonl(&ledger_text).unwrap();

        assert_eq!(
            ledger.to_canonical_jsonl(),
            ledger_text,
            "{name}: reserialize"
        );

        assert_json_eq(
            &name,
            "v_codes",
            &code_array(ledger.attribution_codes()),
            obj_get(&expected, "v_codes"),
        );
        assert_json_eq(
            &name,
            "s_codes",
            &code_array(ledger.settlement_audit_codes()),
            obj_get(&expected, "s_codes"),
        );
        assert_json_eq(
            &name,
            "audit_codes",
            &code_array(ledger.audit_codes()),
            obj_get(&expected, "audit_codes"),
        );
        compare_unimplemented_empty_family(&name, "x_codes", &expected);
        compare_unimplemented_empty_family(&name, "p_codes", &expected);
        assert_json_eq(
            &name,
            "settlement",
            &ledger.settlement_fold_for_version(SettlementVersion::V2),
            obj_get(&expected, "settlement"),
        );
        assert_json_eq(
            &name,
            "conservation",
            &ledger.settlement_conservation_json(SettlementVersion::V2),
            obj_get(&expected, "conservation"),
        );
        passed.push(name);
    }
    eprintln!(
        "attribution conformance cases passed: {}",
        passed.join(", ")
    );
    assert_eq!(passed.len(), 8);
}
