use charge_ledger::{canonical_json, identity, identity_codes, sha256_hex, Json, Ledger};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

const VEC: [(&str, &str, &str, &str); 3] = [
    (
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        "",
        concat!(
            "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555",
            "fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
        ),
    ),
    (
        "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        "72",
        concat!(
            "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da08",
            "5ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
        ),
    ),
    (
        "c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
        "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
        "af82",
        concat!(
            "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18",
            "ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"
        ),
    ),
];

const L_LE: [u8; 32] = [
    0xed, 0xd3, 0xf5, 0x5c, 0x1a, 0x63, 0x12, 0x58, 0xd6, 0x9c, 0xf7, 0xa2, 0xde, 0xf9, 0xde, 0x14,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10,
];

fn hex_to_vec(s: &str) -> Vec<u8> {
    assert_eq!(s.len() % 2, 0);
    let mut out = Vec::with_capacity(s.len() / 2);
    let bytes = s.as_bytes();
    for i in (0..s.len()).step_by(2) {
        out.push((hex_value(bytes[i]) << 4) | hex_value(bytes[i + 1]));
    }
    out
}

fn hex_to_array<const N: usize>(s: &str) -> [u8; N] {
    let v = hex_to_vec(s);
    assert_eq!(v.len(), N);
    let mut out = [0u8; N];
    out.copy_from_slice(&v);
    out
}

fn hex_value(b: u8) -> u8 {
    match b {
        b'0'..=b'9' => b - b'0',
        b'a'..=b'f' => b - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}

fn hex_lower(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        out.push(HEX[(b >> 4) as usize] as char);
        out.push(HEX[(b & 0x0f) as usize] as char);
    }
    out
}

fn obj(fields: &[(&str, Json)]) -> Json {
    Json::Object(
        fields
            .iter()
            .map(|(k, v)| ((*k).to_string(), v.clone()))
            .collect::<BTreeMap<_, _>>(),
    )
}

fn strings(items: &[&str]) -> Json {
    Json::Array(
        items
            .iter()
            .map(|item| Json::String((*item).to_string()))
            .collect(),
    )
}

fn ledger_from_values(values: &[Json]) -> Ledger {
    let mut text = String::new();
    for value in values {
        text.push_str(&canonical_json(value));
        text.push('\n');
    }
    Ledger::parse_jsonl(&text).unwrap()
}

fn event_id(value: &Json) -> String {
    format!("sha256:{}", sha256_hex(canonical_json(value).as_bytes()))
}

fn signed_economy() -> (Ledger, String, String) {
    let seed_a = hex_to_array::<32>(VEC[0].0);
    let seed_b = hex_to_array::<32>(VEC[1].0);
    let (_, pub_a) = identity::keypair(&seed_a).unwrap();
    let (_, pub_b) = identity::keypair(&seed_b).unwrap();
    let issuer = identity::key_author(&pub_a);
    let node = identity::key_author(&pub_b);

    let reg = identity::sign_event(
        &obj(&[
            ("kind", Json::String("register".to_string())),
            ("key", strings(&["exp", &issuer, "reader"])),
            ("subject_entropy_mbits", Json::Int(10_000)),
            ("ceiling_mbits", Json::Int(5_000)),
            ("issuer", Json::String(issuer.clone())),
        ]),
        &seed_a,
    )
    .unwrap();
    let lease = identity::sign_event(
        &obj(&[
            ("kind", Json::String("lease".to_string())),
            ("key", strings(&["exp", &issuer, "reader"])),
            ("lease_seq", Json::Int(1)),
            ("node", Json::String(node.clone())),
            ("amount_mbits", Json::Int(5_000)),
            ("issuer", Json::String(issuer.clone())),
            ("expires_tick", Json::Int(1_000)),
        ]),
        &seed_a,
    )
    .unwrap();
    let lease_id = event_id(&lease);
    let charge = identity::sign_event(
        &obj(&[
            ("kind", Json::String("charge".to_string())),
            ("key", strings(&["exp", &issuer, "reader"])),
            ("node", Json::String(node.clone())),
            ("lease_id", Json::String(lease_id)),
            ("charge_seq", Json::Int(1)),
            ("tick", Json::Int(5)),
            ("channel", Json::String("c".to_string())),
            ("estimate_total_mbits", Json::Int(1_000)),
            ("estimator_id", Json::String("e".to_string())),
            (
                "estimator_independence",
                Json::String("adversarial_review".to_string()),
            ),
            ("estimator_worst_case", Json::Bool(true)),
            ("accepted", Json::Bool(true)),
            ("reason_class", Json::String("EMITTED".to_string())),
            ("reason_detail", Json::String("d".to_string())),
            ("demand_mbits", Json::Int(1_000)),
            ("debit_mbits", Json::Int(1_000)),
        ]),
        &seed_b,
    )
    .unwrap();

    (ledger_from_values(&[reg, lease, charge]), issuer, node)
}

#[test]
fn rfc8032_vectors_exact() {
    for (seed_h, pub_h, msg_h, sig_h) in VEC {
        let seed = hex_to_array::<32>(seed_h);
        let (_, pubkey) = identity::keypair(&seed).unwrap();
        assert_eq!(hex_lower(&pubkey), pub_h);
        let msg = hex_to_vec(msg_h);
        let sig = identity::sign(&seed, &msg).unwrap();
        assert_eq!(hex_lower(&sig), sig_h);
        assert!(identity::verify_sig(&pubkey, &msg, &sig));
        let mut wrong_msg = msg.clone();
        wrong_msg.push(b'x');
        assert!(!identity::verify_sig(&pubkey, &wrong_msg, &sig));
    }
}

#[test]
fn malleability_and_garbage_are_total() {
    let seed = hex_to_array::<32>(VEC[0].0);
    let (_, pubkey) = identity::keypair(&seed).unwrap();
    let sig = identity::sign(&seed, b"m").unwrap();
    let mut forged = sig;
    let mut carry = 0u16;
    for i in 0..32 {
        let sum = forged[32 + i] as u16 + L_LE[i] as u16 + carry;
        forged[32 + i] = sum as u8;
        carry = sum >> 8;
    }
    assert_eq!(carry, 0);
    assert!(!identity::verify_sig(&pubkey, b"m", &forged));

    let bad_cases: Vec<Vec<u8>> = vec![
        Vec::new(),
        vec![0; 63],
        vec![0xff; 64],
        [sig[..32].to_vec(), vec![0xff; 32]].concat(),
        [vec![0xff; 32], sig[32..].to_vec()].concat(),
    ];
    for bad in bad_cases {
        let result = std::panic::catch_unwind(|| identity::verify_sig(&pubkey, b"m", &bad));
        assert!(matches!(result, Ok(false)));
    }
    let result = std::panic::catch_unwind(|| identity::verify_sig(&[0xff; 32], b"m", &sig));
    assert!(matches!(result, Ok(false)));
}

#[test]
fn key_authored_economy_is_clean_and_folds_unmoved() {
    let (ledger, _issuer, _node) = signed_economy();
    assert_eq!(identity_codes(&ledger), Vec::<String>::new());
    assert_eq!(ledger.audit_codes(), Vec::<String>::new());
    let fold = ledger.fold();
    let Json::Object(root) = fold else {
        panic!("fold root");
    };
    let Json::Array(accounts) = root.get("accounts").unwrap() else {
        panic!("accounts");
    };
    assert_eq!(accounts.len(), 1);
}

#[test]
fn a1_missing_sig_ill_formed_key_shape_and_legacy_semantics() {
    let seed = hex_to_array::<32>(VEC[0].0);
    let (_, pubkey) = identity::keypair(&seed).unwrap();
    let issuer = identity::key_author(&pubkey);
    let naked = obj(&[
        ("kind", Json::String("register".to_string())),
        ("key", strings(&["exp", &issuer, "r"])),
        ("subject_entropy_mbits", Json::Int(1_000)),
        ("ceiling_mbits", Json::Int(100)),
        ("issuer", Json::String(issuer.clone())),
    ]);
    let shaped = obj(&[
        ("kind", Json::String("deposit".to_string())),
        ("account", Json::String("x".to_string())),
        ("amount_ucr", Json::Int(1)),
        ("issuer", Json::String("ed25519:nothex".to_string())),
        ("seq", Json::Int(1)),
        ("tick", Json::Int(0)),
    ]);
    let legacy = obj(&[
        ("kind", Json::String("deposit".to_string())),
        ("account", Json::String("x".to_string())),
        ("amount_ucr", Json::Int(1)),
        ("issuer", Json::String("bob".to_string())),
        ("seq", Json::Int(2)),
        ("tick", Json::Int(0)),
    ]);
    let inert_sig_unknown_kind = obj(&[
        ("kind", Json::String("derivation".to_string())),
        ("issuer", Json::String(issuer.clone())),
    ]);
    let ledger = ledger_from_values(&[naked, shaped, legacy, inert_sig_unknown_kind]);
    let codes = identity_codes(&ledger);
    assert_eq!(codes.len(), 2, "{codes:?}");
    assert!(codes.iter().all(|c| c.starts_with("A1 ")), "{codes:?}");
    assert!(codes.iter().any(|c| c == &format!("A1 {issuer}")));
    assert!(codes.iter().any(|c| c == "A1 ed25519:nothex"));
}

#[test]
fn a2_wrong_transplanted_and_attacker_signatures() {
    let (ledger, issuer, _) = signed_economy();
    let mut events = Vec::new();
    for line in ledger.to_canonical_jsonl().lines() {
        events.push(charge_ledger::parse_json(line).unwrap());
    }
    let reg = events
        .iter()
        .find(|v| identity::author_of(v) == Some(issuer.as_str()))
        .unwrap();
    let lease_sig = events
        .iter()
        .find_map(|v| match v {
            Json::Object(fields)
                if fields.get("kind") == Some(&Json::String("lease".to_string())) =>
            {
                fields.get("sig").cloned()
            }
            _ => None,
        })
        .unwrap();
    let mut forged_reg = match reg {
        Json::Object(fields) => fields.clone(),
        _ => panic!("object"),
    };
    forged_reg.insert("ceiling_mbits".to_string(), Json::Int(999_999));
    forged_reg.insert("sig".to_string(), lease_sig);

    let attacker_seed = [7u8; 32];
    let attacker_payload = obj(&[
        ("kind", Json::String("deposit".to_string())),
        ("account", Json::String("attacker".to_string())),
        ("amount_ucr", Json::Int(1_000_000_000)),
        ("issuer", Json::String(issuer.clone())),
        ("seq", Json::Int(1)),
        ("tick", Json::Int(0)),
    ]);
    let mut attacker_obj = match attacker_payload {
        Json::Object(fields) => fields,
        _ => unreachable!(),
    };
    let sig = identity::sign(
        &attacker_seed,
        &identity::signed_bytes(&Json::Object(attacker_obj.clone())),
    )
    .unwrap();
    attacker_obj.insert("sig".to_string(), Json::String(hex_lower(&sig)));

    events.push(Json::Object(forged_reg));
    events.push(Json::Object(attacker_obj));
    let codes = identity_codes(&ledger_from_values(&events));
    assert_eq!(codes, vec![format!("A2 {issuer}")]);
}

#[test]
fn sign_event_refuses_author_mismatch() {
    let seed = hex_to_array::<32>(VEC[0].0);
    let payload = obj(&[
        ("kind", Json::String("deposit".to_string())),
        ("account", Json::String("x".to_string())),
        ("amount_ucr", Json::Int(1)),
        ("issuer", Json::String("bob".to_string())),
        ("seq", Json::Int(1)),
        ("tick", Json::Int(0)),
    ]);
    let err = identity::sign_event(&payload, &seed).unwrap_err();
    assert!(err.contains("not this key's id"), "{err}");
}

#[test]
fn uppercase_author_hex_is_a1_even_with_valid_sig_bytes() {
    // Flipped 2026-07-09: this lane originally pinned the reference's
    // hex-decoding tolerance (uppercase author verifies → clean). That
    // tolerance WAS the aliasing seam; spec and both implementations
    // now refuse it, so the same artifact convicts A1.
    let seed = hex_to_array::<32>(VEC[0].0);
    let (_, pubkey) = identity::keypair(&seed).unwrap();
    let lower = identity::key_author(&pubkey);
    let issuer = format!(
        "ed25519:{}",
        lower[identity::KEY_PREFIX.len()..].to_uppercase()
    );
    let mut fields = match obj(&[
        ("kind", Json::String("deposit".to_string())),
        ("account", Json::String("x".to_string())),
        ("amount_ucr", Json::Int(1)),
        ("issuer", Json::String(issuer)),
        ("seq", Json::Int(1)),
        ("tick", Json::Int(0)),
    ]) {
        Json::Object(fields) => fields,
        _ => unreachable!(),
    };
    let unsigned = Json::Object(fields.clone());
    let sig = identity::sign(&seed, &identity::signed_bytes(&unsigned)).unwrap();
    fields.insert("sig".to_string(), Json::String(hex_lower(&sig)));
    let issuer = match fields.get("issuer") {
        Some(Json::String(s)) => s.clone(),
        _ => unreachable!(),
    };
    let ledger = ledger_from_values(&[Json::Object(fields)]);
    assert_eq!(identity_codes(&ledger), vec![format!("A1 {issuer}")]);
}

#[test]
fn frozen_corpora_have_zero_a_codes() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
    let dirs = [
        root.join("ledger_traces"),
        root.join("settlement_traces"),
        root.join("settlement2_traces"),
    ];
    let mut checked = 0;
    for dir in dirs {
        for entry in fs::read_dir(dir).unwrap() {
            let path = entry.unwrap().path();
            if path.extension().and_then(|s| s.to_str()) != Some("jsonl") {
                continue;
            }
            if !path
                .file_name()
                .unwrap()
                .to_string_lossy()
                .ends_with(".ledger.jsonl")
            {
                continue;
            }
            let text = fs::read_to_string(&path).unwrap();
            let ledger = Ledger::parse_jsonl(&text).unwrap();
            assert_eq!(
                ledger.to_canonical_jsonl(),
                text,
                "{} reserialize",
                path.display()
            );
            assert_eq!(
                identity_codes(&ledger),
                Vec::<String>::new(),
                "{}",
                path.display()
            );
            checked += 1;
        }
    }
    assert_eq!(checked, 46);
}

#[test]
fn charge_verify_convicts_a_codes() {
    let seed = hex_to_array::<32>(VEC[0].0);
    let (_, pubkey) = identity::keypair(&seed).unwrap();
    let issuer = identity::key_author(&pubkey);
    let naked = obj(&[
        ("kind", Json::String("register".to_string())),
        ("key", strings(&["exp", &issuer, "r"])),
        ("subject_entropy_mbits", Json::Int(1_000)),
        ("ceiling_mbits", Json::Int(100)),
        ("issuer", Json::String(issuer)),
    ]);
    let text = format!("{}\n", canonical_json(&naked));
    let path: PathBuf = std::env::temp_dir().join(format!(
        "charge-ledger-a-code-{}-{}.jsonl",
        std::process::id(),
        1
    ));
    fs::write(&path, text).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_charge-verify"))
        .arg(&path)
        .output()
        .unwrap();
    let _ = fs::remove_file(&path);
    assert!(!output.status.success());
    assert_eq!(output.status.code(), Some(1));
    let stdout = String::from_utf8(output.stdout).unwrap();
    assert!(stdout.contains("identity findings:"), "{stdout}");
    assert!(stdout.contains("A1 ed25519:"), "{stdout}");
    assert!(stdout.contains("CONVICTED:"), "{stdout}");
}

#[test]
fn case_alias_is_a1_never_a_second_namespace() {
    // The aliasing seam (named and closed 2026-07-09): tolerant hex
    // decoding let `ed25519:ABC…` verify against the same key as
    // `ed25519:abc…` — two author namespaces with disjoint
    // (author, kind, seq) spaces, equivocation across them invisible
    // to X0. Well-formed is lowercase EXACTLY; every case-alias
    // convicts A1 even when the signature bytes verify.
    let seed = hex_to_array::<32>(VEC[0].0);
    let (_, pubkey) = identity::keypair(&seed).unwrap();
    let lower = identity::key_author(&pubkey);
    let upper = format!("ed25519:{}", lower["ed25519:".len()..].to_uppercase());
    assert_ne!(lower, upper);

    let signed = identity::sign_event(
        &obj(&[
            ("kind", Json::String("register".to_string())),
            ("key", strings(&["exp", &lower, "reader"])),
            ("subject_entropy_mbits", Json::Int(1_000)),
            ("ceiling_mbits", Json::Int(100)),
            ("issuer", Json::String(lower.clone())),
        ]),
        &seed,
    )
    .unwrap();

    // The alias: same key, freshly valid signature bytes, uppercase id.
    let mut alias = signed.clone();
    if let Json::Object(map) = &mut alias {
        map.insert("issuer".to_string(), Json::String(upper.clone()));
        map.remove("sig");
    }
    let sig = identity::sign(&seed, &identity::signed_bytes(&alias)).unwrap();
    if let Json::Object(map) = &mut alias {
        map.insert("sig".to_string(), Json::String(hex_lower(&sig)));
    }

    let ledger = ledger_from_values(&[signed.clone(), alias]);
    assert_eq!(identity_codes(&ledger), vec![format!("A1 {upper}")]);

    // And the sig field itself accepts exactly one encoding.
    let mut upsig = signed;
    if let Json::Object(map) = &mut upsig {
        let s = match map.get("sig") {
            Some(Json::String(s)) => s.to_uppercase(),
            _ => unreachable!(),
        };
        map.insert("sig".to_string(), Json::String(s));
    }
    let ledger2 = ledger_from_values(&[upsig]);
    assert_eq!(identity_codes(&ledger2), vec![format!("A1 {lower}")]);
}
