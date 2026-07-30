//! Independent second implementation of `egress-accountant/1`.
//!
//! Written from `../SPEC.md` alone — integer millibits (`i64`), no floating
//! point in the decision path, no third-party dependencies. The minimal JSON
//! reader/writer below is scoped to the golden-trace format only, so this crate
//! shares no code and no libraries with the Python reference. If this
//! implementation and the reference disagree on any trace, that is a finding:
//! a bug in one, or an ambiguity in the spec.

use std::collections::BTreeMap;

// ---- constants (SPEC §1.3, §1.5) ----

const VALID_INDEPENDENCE: [&str; 3] = ["operator", "role_separated", "adversarial_review"];

const NEGLIGIBLE_PERMILLE: i64 = 50;
const BOUNDED_PERMILLE: i64 = 250;
const MATERIAL_PERMILLE: i64 = 500;
const UNSAFE_PERMILLE: i64 = 800;

// ---- data model (SPEC §1) ----

#[derive(Clone, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct CompositionKey {
    pub subject: String,
    pub query_family: String,
    pub audience: String,
}

#[derive(Clone, Debug)]
pub struct CapacityEstimate {
    pub enum_value_mbits: i64,
    pub ordering_mbits: i64,
    pub field_presence_mbits: i64,
    pub text_mbits: i64,
    pub side_channel_mbits: i64,
    pub channel: String,
}

impl CapacityEstimate {
    pub fn total_mbits(&self) -> i64 {
        self.enum_value_mbits
            + self.ordering_mbits
            + self.field_presence_mbits
            + self.text_mbits
            + self.side_channel_mbits
    }
}

#[derive(Clone, Debug)]
pub struct EstimatorAttestation {
    pub estimator_id: String,
    pub independence: String,
    pub method: String,
    pub worst_case_over_secrets: bool,
}

impl EstimatorAttestation {
    /// SPEC §1.3 — ordered checks; the first failing one supplies the reason.
    fn admissibility(&self) -> (bool, &'static str) {
        if self.independence == "self_interested" {
            return (false, "self_interested_estimator");
        }
        if !VALID_INDEPENDENCE.contains(&self.independence.as_str()) {
            return (false, "unknown_independence_class");
        }
        if !self.worst_case_over_secrets {
            return (false, "estimate_not_worst_case");
        }
        (true, "")
    }
}

#[derive(Clone, Debug)]
struct CompositionState {
    subject_entropy_mbits: i64,
    ceiling_mbits: i64,
    cumulative_mbits: i64,
    demanded_mbits: i64,
    blocked: bool,
    incident: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Decision {
    pub accepted: bool,
    pub reason_class: String,
    pub reason_detail: String,
    pub cumulative_mbits: i64,
    pub demanded_mbits: i64,
    pub blocked: bool,
    pub incident: bool,
    pub leakage_class: String,
    pub newly_incident: bool,
}

impl Decision {
    pub fn to_json(&self) -> String {
        format!(
            "{{\"accepted\":{},\"reason_class\":{},\"reason_detail\":{},\
             \"cumulative_mbits\":{},\"demanded_mbits\":{},\"blocked\":{},\
             \"incident\":{},\"leakage_class\":{},\"newly_incident\":{}}}",
            self.accepted,
            json_str(&self.reason_class),
            json_str(&self.reason_detail),
            self.cumulative_mbits,
            self.demanded_mbits,
            self.blocked,
            self.incident,
            json_str(&self.leakage_class),
            self.newly_incident,
        )
    }
}

// ---- leakage class: integer cross-multiplication, no division (SPEC §1.5) ----

fn leakage_class(cumulative_mbits: i64, subject_entropy_mbits: i64) -> &'static str {
    let c = cumulative_mbits.min(subject_entropy_mbits); // cap the fraction at 1
    let s = subject_entropy_mbits;
    if c * 1000 <= NEGLIGIBLE_PERMILLE * s {
        "negligible"
    } else if c * 1000 <= BOUNDED_PERMILLE * s {
        "bounded"
    } else if c * 1000 <= MATERIAL_PERMILLE * s {
        "material"
    } else if c * 1000 <= UNSAFE_PERMILLE * s {
        "unsafe"
    } else {
        "reconstructed"
    }
}

// ---- the accountant (SPEC §2) ----

pub struct EgressAccountant {
    states: BTreeMap<CompositionKey, CompositionState>,
}

impl EgressAccountant {
    pub fn new() -> Self {
        EgressAccountant { states: BTreeMap::new() }
    }

    /// SPEC §2.1 — idempotent create; never resets an existing state.
    pub fn register(&mut self, key: CompositionKey, subject_entropy_mbits: i64, ceiling_mbits: i64) {
        self.states.entry(key).or_insert(CompositionState {
            subject_entropy_mbits,
            ceiling_mbits,
            cumulative_mbits: 0,
            demanded_mbits: 0,
            blocked: false,
            incident: false,
        });
    }

    /// SPEC §2.2 — steps A..E, in order; the first that returns, returns.
    pub fn charge(
        &mut self,
        key: &CompositionKey,
        estimate: &CapacityEstimate,
        estimator: &EstimatorAttestation,
        _tick: i64,
    ) -> Decision {
        let st = self.states.get_mut(key).expect("charge on unregistered key");

        // Step A — estimator admissibility (no counter moves).
        let (ok, reason) = estimator.admissibility();
        if !ok {
            return Decision {
                accepted: false,
                reason_class: "REFUSED_ESTIMATOR".to_string(),
                reason_detail: reason.to_string(),
                cumulative_mbits: st.cumulative_mbits,
                demanded_mbits: st.demanded_mbits,
                blocked: st.blocked,
                incident: st.incident,
                leakage_class: leakage_class(st.cumulative_mbits, st.subject_entropy_mbits).to_string(),
                newly_incident: false,
            };
        }

        // Step B — accrue demand, evaluate incident on UNCAPPED demand.
        let bits = estimate.total_mbits();
        st.demanded_mbits += bits;
        let newly_incident =
            !st.incident && st.demanded_mbits * 1000 >= UNSAFE_PERMILLE * st.subject_entropy_mbits;
        if newly_incident {
            st.incident = true;
        }

        // Step C — already blocked.
        if st.blocked {
            return Decision {
                accepted: false,
                reason_class: "REFUSED_BLOCKED".to_string(),
                reason_detail: "budget_already_blocked".to_string(),
                cumulative_mbits: st.cumulative_mbits,
                demanded_mbits: st.demanded_mbits,
                blocked: true,
                incident: st.incident,
                leakage_class: leakage_class(st.cumulative_mbits, st.subject_entropy_mbits).to_string(),
                newly_incident,
            };
        }

        // Step D — would exceed the ceiling (strict >).
        let remaining = (st.ceiling_mbits - st.cumulative_mbits).max(0);
        if bits > remaining {
            st.blocked = true;
            return Decision {
                accepted: false,
                reason_class: "REFUSED_CEILING".to_string(),
                reason_detail: "would_exceed_ceiling".to_string(),
                cumulative_mbits: st.cumulative_mbits,
                demanded_mbits: st.demanded_mbits,
                blocked: true,
                incident: st.incident,
                leakage_class: leakage_class(st.cumulative_mbits, st.subject_entropy_mbits).to_string(),
                newly_incident,
            };
        }

        // Step E — emit.
        st.cumulative_mbits += bits;
        if st.cumulative_mbits >= st.ceiling_mbits {
            st.blocked = true;
        }
        Decision {
            accepted: true,
            reason_class: "EMITTED".to_string(),
            reason_detail: "emitted_debited".to_string(),
            cumulative_mbits: st.cumulative_mbits,
            demanded_mbits: st.demanded_mbits,
            blocked: st.blocked,
            incident: st.incident,
            leakage_class: leakage_class(st.cumulative_mbits, st.subject_entropy_mbits).to_string(),
            newly_incident,
        }
    }
}

impl Default for EgressAccountant {
    fn default() -> Self {
        Self::new()
    }
}

// ---- trace replay (SPEC §3) ----

pub struct Trace {
    pub name: String,
    pub ops: Vec<Json>,
    pub expected: Vec<Json>,
}

/// Replay a trace's ops through a fresh accountant, returning the Decision
/// stream (one per `charge` op, in order).
pub fn replay(trace: &Trace) -> Vec<Decision> {
    let mut acc = EgressAccountant::new();
    let mut out = Vec::new();
    for op in &trace.ops {
        let key = parse_key(op.get("key"));
        match op.get("op").as_str() {
            "register" => acc.register(
                key,
                op.get("subject_entropy_mbits").as_i64(),
                op.get("ceiling_mbits").as_i64(),
            ),
            "charge" => {
                let e = op.get("estimate");
                let estimate = CapacityEstimate {
                    enum_value_mbits: e.get("enum_value_mbits").as_i64(),
                    ordering_mbits: e.get("ordering_mbits").as_i64(),
                    field_presence_mbits: e.get("field_presence_mbits").as_i64(),
                    text_mbits: e.get("text_mbits").as_i64(),
                    side_channel_mbits: e.get("side_channel_mbits").as_i64(),
                    channel: e.get("channel").as_str().to_string(),
                };
                let a = op.get("estimator");
                let estimator = EstimatorAttestation {
                    estimator_id: a.get("estimator_id").as_str().to_string(),
                    independence: a.get("independence").as_str().to_string(),
                    method: a.get("method").as_str().to_string(),
                    worst_case_over_secrets: a.get("worst_case_over_secrets").as_bool(),
                };
                out.push(acc.charge(&key, &estimate, &estimator, op.get("tick").as_i64()));
            }
            other => panic!("unknown op {other:?}"),
        }
    }
    out
}

fn parse_key(v: &Json) -> CompositionKey {
    let a = v.as_arr();
    CompositionKey {
        subject: a[0].as_str().to_string(),
        query_family: a[1].as_str().to_string(),
        audience: a[2].as_str().to_string(),
    }
}

/// Compare a produced Decision to an `expected` JSON object field-by-field.
/// Returns the name of the first diverging field, or None if all agree.
pub fn diff_decision(actual: &Decision, expected: &Json) -> Option<String> {
    let checks: [(&str, bool); 9] = [
        ("accepted", expected.get("accepted").as_bool() == actual.accepted),
        ("reason_class", expected.get("reason_class").as_str() == actual.reason_class),
        ("reason_detail", expected.get("reason_detail").as_str() == actual.reason_detail),
        ("cumulative_mbits", expected.get("cumulative_mbits").as_i64() == actual.cumulative_mbits),
        ("demanded_mbits", expected.get("demanded_mbits").as_i64() == actual.demanded_mbits),
        ("blocked", expected.get("blocked").as_bool() == actual.blocked),
        ("incident", expected.get("incident").as_bool() == actual.incident),
        ("leakage_class", expected.get("leakage_class").as_str() == actual.leakage_class),
        ("newly_incident", expected.get("newly_incident").as_bool() == actual.newly_incident),
    ];
    checks.iter().find(|(_, ok)| !ok).map(|(f, _)| f.to_string())
}

// ---- minimal JSON (scoped to the trace format; std-only) ----

#[derive(Clone, Debug)]
pub enum Json {
    Null,
    Bool(bool),
    Int(i64),
    Str(String),
    Arr(Vec<Json>),
    Obj(BTreeMap<String, Json>),
}

impl Json {
    pub fn get(&self, key: &str) -> &Json {
        match self {
            Json::Obj(m) => m.get(key).unwrap_or(&Json::Null),
            _ => &Json::Null,
        }
    }
    pub fn as_str(&self) -> &str {
        match self {
            Json::Str(s) => s,
            _ => panic!("not a string: {self:?}"),
        }
    }
    pub fn as_i64(&self) -> i64 {
        match self {
            Json::Int(n) => *n,
            _ => panic!("not an int: {self:?}"),
        }
    }
    pub fn as_bool(&self) -> bool {
        match self {
            Json::Bool(b) => *b,
            _ => panic!("not a bool: {self:?}"),
        }
    }
    pub fn as_arr(&self) -> &[Json] {
        match self {
            Json::Arr(a) => a,
            _ => panic!("not an array: {self:?}"),
        }
    }
}

struct P<'a> {
    b: &'a [u8],
    i: usize,
}

impl<'a> P<'a> {
    fn ws(&mut self) {
        while self.i < self.b.len() && matches!(self.b[self.i], b' ' | b'\t' | b'\n' | b'\r') {
            self.i += 1;
        }
    }
    fn val(&mut self) -> Json {
        self.ws();
        match self.b[self.i] {
            b'{' => self.obj(),
            b'[' => self.arr(),
            b'"' => Json::Str(self.string()),
            b't' => {
                self.i += 4;
                Json::Bool(true)
            }
            b'f' => {
                self.i += 5;
                Json::Bool(false)
            }
            b'n' => {
                self.i += 4;
                Json::Null
            }
            _ => self.number(),
        }
    }
    fn obj(&mut self) -> Json {
        let mut m = BTreeMap::new();
        self.i += 1; // {
        self.ws();
        if self.b[self.i] == b'}' {
            self.i += 1;
            return Json::Obj(m);
        }
        loop {
            self.ws();
            let k = self.string();
            self.ws();
            self.i += 1; // :
            let v = self.val();
            m.insert(k, v);
            self.ws();
            let c = self.b[self.i];
            self.i += 1; // , or }
            if c == b'}' {
                break;
            }
        }
        Json::Obj(m)
    }
    fn arr(&mut self) -> Json {
        let mut a = Vec::new();
        self.i += 1; // [
        self.ws();
        if self.b[self.i] == b']' {
            self.i += 1;
            return Json::Arr(a);
        }
        loop {
            a.push(self.val());
            self.ws();
            let c = self.b[self.i];
            self.i += 1; // , or ]
            if c == b']' {
                break;
            }
        }
        Json::Arr(a)
    }
    fn string(&mut self) -> String {
        self.i += 1; // opening "
        let mut s = String::new();
        while self.b[self.i] != b'"' {
            if self.b[self.i] == b'\\' {
                self.i += 1;
                let e = self.b[self.i];
                match e {
                    b'"' => s.push('"'),
                    b'\\' => s.push('\\'),
                    b'/' => s.push('/'),
                    b'n' => s.push('\n'),
                    b't' => s.push('\t'),
                    b'r' => s.push('\r'),
                    b'b' => s.push('\u{08}'),
                    b'f' => s.push('\u{0C}'),
                    b'u' => {
                        let hex = std::str::from_utf8(&self.b[self.i + 1..self.i + 5]).unwrap();
                        let cp = u32::from_str_radix(hex, 16).unwrap();
                        s.push(char::from_u32(cp).unwrap_or('\u{FFFD}'));
                        self.i += 4;
                    }
                    _ => s.push(e as char),
                }
                self.i += 1;
            } else {
                // handle multi-byte UTF-8 by copying raw bytes to a buffer
                let start = self.i;
                while self.b[self.i] != b'"' && self.b[self.i] != b'\\' {
                    self.i += 1;
                }
                s.push_str(std::str::from_utf8(&self.b[start..self.i]).unwrap());
            }
        }
        self.i += 1; // closing "
        s
    }
    fn number(&mut self) -> Json {
        let start = self.i;
        if self.b[self.i] == b'-' {
            self.i += 1;
        }
        while self.i < self.b.len() && self.b[self.i].is_ascii_digit() {
            self.i += 1;
        }
        let text = std::str::from_utf8(&self.b[start..self.i]).unwrap();
        Json::Int(text.parse::<i64>().expect("trace numbers are integers"))
    }
}

pub fn parse_json(s: &str) -> Json {
    let mut p = P { b: s.as_bytes(), i: 0 };
    p.val()
}

fn json_str(s: &str) -> String {
    let mut out = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\t' => out.push_str("\\t"),
            '\r' => out.push_str("\\r"),
            _ => out.push(c),
        }
    }
    out.push('"');
    out
}

/// Load a trace file into a `Trace` (name + ops + expected).
pub fn load_trace(text: &str) -> Trace {
    let j = parse_json(text);
    Trace {
        name: j.get("name").as_str().to_string(),
        ops: j.get("ops").as_arr().to_vec(),
        expected: j.get("expected").as_arr().to_vec(),
    }
}
