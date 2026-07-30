use charge_ledger::{canonical_json, parse_json, Json, Ledger, SettlementVersion};
use std::fs;
use std::path::{Path, PathBuf};

fn corpus_dirs() -> Vec<PathBuf> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
    vec![
        root.join("settlement_traces"),
        root.join("settlement2_traces"),
    ]
}

fn obj_get<'a>(value: &'a Json, key: &str) -> &'a Json {
    match value {
        Json::Object(fields) => fields.get(key).unwrap(),
        _ => panic!("expected object"),
    }
}

fn str_field<'a>(value: &'a Json, key: &str) -> &'a str {
    match obj_get(value, key) {
        Json::String(s) => s,
        _ => panic!("expected string field"),
    }
}

fn settlement_version(expected: &Json) -> SettlementVersion {
    match str_field(expected, "spec") {
        "charge-settlement/1" => SettlementVersion::V1,
        "charge-settlement/2" => SettlementVersion::V2,
        spec => panic!("unknown settlement spec {spec}"),
    }
}

fn case_paths() -> Vec<(String, PathBuf)> {
    let mut paths = Vec::new();
    for dir in corpus_dirs() {
        for entry in fs::read_dir(dir).unwrap() {
            let path = entry.unwrap().path();
            let file = path.file_name().unwrap().to_string_lossy();
            if let Some(name) = file.strip_suffix(".ledger.jsonl") {
                paths.push((name.to_string(), path));
            }
        }
    }
    paths.sort_by(|a, b| a.0.cmp(&b.0).then_with(|| a.1.cmp(&b.1)));
    paths
}

#[test]
fn settlement_conformance() {
    let mut passed = Vec::new();
    for (name, ledger_path) in case_paths() {
        let expected_path = ledger_path.with_file_name(format!("{name}.expected.json"));
        let ledger_text = fs::read_to_string(&ledger_path).unwrap();
        let expected_text = fs::read_to_string(expected_path).unwrap();
        let expected = parse_json(&expected_text).unwrap();
        let version = settlement_version(&expected);

        let ledger = Ledger::parse_jsonl(&ledger_text).unwrap();
        assert_eq!(
            ledger.to_canonical_jsonl(),
            ledger_text,
            "{name}: reserialize"
        );

        let settlement = ledger.settlement_fold_for_version(version);
        let expected_settlement = obj_get(&expected, "settlement");
        assert_eq!(settlement, *expected_settlement, "{name}: settlement");
        assert_eq!(
            canonical_json(&settlement),
            canonical_json(expected_settlement),
            "{name}: settlement canonical string"
        );

        let s_codes = Json::Array(
            ledger
                .settlement_audit_codes()
                .into_iter()
                .map(Json::String)
                .collect::<Vec<_>>(),
        );
        assert_eq!(s_codes, *obj_get(&expected, "s_codes"), "{name}: s_codes");

        let audit_codes = Json::Array(
            ledger
                .audit_codes()
                .into_iter()
                .map(Json::String)
                .collect::<Vec<_>>(),
        );
        assert_eq!(
            audit_codes,
            *obj_get(&expected, "audit_codes"),
            "{name}: audit_codes"
        );

        assert_eq!(
            ledger.settlement_conservation_json(version),
            *obj_get(&expected, "conservation"),
            "{name}: conservation"
        );
        passed.push(name);
    }
    eprintln!("settlement conformance cases passed: {}", passed.join(", "));
    // 13 /1 + 17 /2 scenarios (3 adversarial soups 2026-07-06: conservation
    // + totality pinned as corpus after the fable review caught the port
    // reproducing the pre-fix spec's F1 bug verbatim; +1 g19 named-override
    // referent 2026-07-07: the naming binds — a port that keeps scanning
    // when a referent is named diverges on it).
    assert_eq!(passed.len(), 30);
}
