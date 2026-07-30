use std::collections::{BTreeMap, BTreeSet};

pub mod identity;
pub use identity::identity_codes;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum Json {
    Null,
    Bool(bool),
    Int(i64),
    String(String),
    Array(Vec<Json>),
    Object(BTreeMap<String, Json>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Event {
    pub id: String,
    pub value: Json,
    canonical: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Ledger {
    events: BTreeMap<String, Event>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LedgerError {
    Json(String),
    ContentAddressViolation(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Account {
    pub key: Vec<String>,
    pub subject_entropy_mbits: i64,
    pub ceiling_mbits: i64,
    pub cumulative_mbits: i64,
    pub demanded_mbits: i64,
    pub granted_lease_mbits: i64,
    pub leakage_class: String,
    pub incident: bool,
    pub conflicted: bool,
}

fn obj_get<'a>(value: &'a Json, key: &str) -> Option<&'a Json> {
    match value {
        Json::Object(fields) => fields.get(key),
        _ => None,
    }
}

fn kind(value: &Json) -> Option<&str> {
    match obj_get(value, "kind") {
        Some(Json::String(s)) => Some(s.as_str()),
        _ => None,
    }
}

fn as_int(value: Option<&Json>) -> Option<i64> {
    match value {
        Some(Json::Int(n)) => Some(*n),
        _ => None,
    }
}

fn as_uint(value: Option<&Json>) -> Option<i64> {
    match value {
        Some(Json::Int(n)) if *n >= 0 => Some(*n),
        _ => None,
    }
}

fn as_string(value: Option<&Json>) -> Option<&str> {
    match value {
        Some(Json::String(s)) => Some(s.as_str()),
        _ => None,
    }
}

fn as_bool(value: Option<&Json>) -> Option<bool> {
    match value {
        Some(Json::Bool(b)) => Some(*b),
        _ => None,
    }
}

fn as_key(value: Option<&Json>) -> Option<Vec<String>> {
    match value {
        Some(Json::Array(items)) => {
            let mut out = Vec::with_capacity(items.len());
            for item in items {
                match item {
                    Json::String(s) => out.push(s.clone()),
                    _ => return None,
                }
            }
            Some(out)
        }
        _ => None,
    }
}

fn json_string_array(strings: &[String]) -> Json {
    Json::Array(strings.iter().cloned().map(Json::String).collect())
}

pub fn canonical_json(value: &Json) -> String {
    let mut out = String::new();
    write_canonical_json(value, &mut out);
    out
}

fn write_canonical_json(value: &Json, out: &mut String) {
    match value {
        Json::Null => out.push_str("null"),
        Json::Bool(true) => out.push_str("true"),
        Json::Bool(false) => out.push_str("false"),
        Json::Int(n) => out.push_str(&n.to_string()),
        Json::String(s) => write_json_string(s, out),
        Json::Array(items) => {
            out.push('[');
            for (idx, item) in items.iter().enumerate() {
                if idx != 0 {
                    out.push(',');
                }
                write_canonical_json(item, out);
            }
            out.push(']');
        }
        Json::Object(fields) => {
            out.push('{');
            for (idx, (key, item)) in fields.iter().enumerate() {
                if idx != 0 {
                    out.push(',');
                }
                write_json_string(key, out);
                out.push(':');
                write_canonical_json(item, out);
            }
            out.push('}');
        }
    }
}

fn write_json_string(s: &str, out: &mut String) {
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{08}' => out.push_str("\\b"),
            '\u{0c}' => out.push_str("\\f"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            ch if ch <= '\u{1f}' => {
                out.push_str("\\u");
                push_hex4(out, ch as u32);
            }
            ch if ch.is_ascii() => out.push(ch),
            ch => {
                let code = ch as u32;
                if code <= 0xffff {
                    out.push_str("\\u");
                    push_hex4(out, code);
                } else {
                    let m = code - 0x10000;
                    let high = 0xd800 + (m >> 10);
                    let low = 0xdc00 + (m & 0x3ff);
                    out.push_str("\\u");
                    push_hex4(out, high);
                    out.push_str("\\u");
                    push_hex4(out, low);
                }
            }
        }
    }
    out.push('"');
}

fn push_hex4(out: &mut String, n: u32) {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    for shift in [12, 8, 4, 0] {
        out.push(HEX[((n >> shift) & 0xf) as usize] as char);
    }
}

pub fn parse_json(input: &str) -> Result<Json, LedgerError> {
    let mut parser = Parser::new(input);
    let value = parser.parse_value()?;
    parser.skip_ws();
    if parser.is_eof() {
        Ok(value)
    } else {
        Err(LedgerError::Json("trailing characters".to_string()))
    }
}

struct Parser<'a> {
    input: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            input: input.as_bytes(),
            pos: 0,
        }
    }

    fn is_eof(&self) -> bool {
        self.pos >= self.input.len()
    }

    fn peek(&self) -> Option<u8> {
        self.input.get(self.pos).copied()
    }

    fn bump(&mut self) -> Option<u8> {
        let b = self.peek()?;
        self.pos += 1;
        Some(b)
    }

    fn skip_ws(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\n' | b'\r' | b'\t')) {
            self.pos += 1;
        }
    }

    fn parse_value(&mut self) -> Result<Json, LedgerError> {
        self.skip_ws();
        match self.peek() {
            Some(b'n') => self.parse_literal(b"null", Json::Null),
            Some(b't') => self.parse_literal(b"true", Json::Bool(true)),
            Some(b'f') => self.parse_literal(b"false", Json::Bool(false)),
            Some(b'"') => Ok(Json::String(self.parse_string()?)),
            Some(b'[') => self.parse_array(),
            Some(b'{') => self.parse_object(),
            Some(b'-' | b'0'..=b'9') => self.parse_int(),
            _ => Err(LedgerError::Json(format!(
                "unexpected byte at position {}",
                self.pos
            ))),
        }
    }

    fn parse_literal(&mut self, literal: &[u8], value: Json) -> Result<Json, LedgerError> {
        if self.input.get(self.pos..self.pos + literal.len()) == Some(literal) {
            self.pos += literal.len();
            Ok(value)
        } else {
            Err(LedgerError::Json(format!(
                "invalid literal at position {}",
                self.pos
            )))
        }
    }

    fn parse_string(&mut self) -> Result<String, LedgerError> {
        if self.bump() != Some(b'"') {
            return Err(LedgerError::Json("expected string".to_string()));
        }
        let mut bytes = Vec::new();
        while let Some(b) = self.bump() {
            match b {
                b'"' => {
                    return String::from_utf8(bytes)
                        .map_err(|_| LedgerError::Json("invalid utf-8 string".to_string()));
                }
                b'\\' => match self.bump() {
                    Some(b'"') => bytes.push(b'"'),
                    Some(b'\\') => bytes.push(b'\\'),
                    Some(b'/') => bytes.push(b'/'),
                    Some(b'b') => bytes.push(0x08),
                    Some(b'f') => bytes.push(0x0c),
                    Some(b'n') => bytes.push(b'\n'),
                    Some(b'r') => bytes.push(b'\r'),
                    Some(b't') => bytes.push(b'\t'),
                    Some(b'u') => {
                        let unit = self.parse_hex4()?;
                        let ch = if (0xd800..=0xdbff).contains(&unit) {
                            if self.bump() != Some(b'\\') || self.bump() != Some(b'u') {
                                return Err(LedgerError::Json("missing low surrogate".to_string()));
                            }
                            let low = self.parse_hex4()?;
                            if !(0xdc00..=0xdfff).contains(&low) {
                                return Err(LedgerError::Json("invalid low surrogate".to_string()));
                            }
                            let code = 0x10000
                                + (((unit - 0xd800) as u32) << 10)
                                + ((low - 0xdc00) as u32);
                            char::from_u32(code).ok_or_else(|| {
                                LedgerError::Json("invalid surrogate pair".to_string())
                            })?
                        } else if (0xdc00..=0xdfff).contains(&unit) {
                            return Err(LedgerError::Json("unpaired low surrogate".to_string()));
                        } else {
                            char::from_u32(unit as u32).ok_or_else(|| {
                                LedgerError::Json("invalid unicode escape".to_string())
                            })?
                        };
                        let mut tmp = [0u8; 4];
                        bytes.extend_from_slice(ch.encode_utf8(&mut tmp).as_bytes());
                    }
                    _ => return Err(LedgerError::Json("invalid escape".to_string())),
                },
                0x00..=0x1f => {
                    return Err(LedgerError::Json("unescaped control character".to_string()))
                }
                _ => bytes.push(b),
            }
        }
        Err(LedgerError::Json("unterminated string".to_string()))
    }

    fn parse_hex4(&mut self) -> Result<u16, LedgerError> {
        let mut n: u16 = 0;
        for _ in 0..4 {
            let b = self
                .bump()
                .ok_or_else(|| LedgerError::Json("truncated unicode escape".to_string()))?;
            n = (n << 4)
                | match b {
                    b'0'..=b'9' => (b - b'0') as u16,
                    b'a'..=b'f' => (b - b'a' + 10) as u16,
                    b'A'..=b'F' => (b - b'A' + 10) as u16,
                    _ => return Err(LedgerError::Json("invalid hex escape".to_string())),
                };
        }
        Ok(n)
    }

    fn parse_array(&mut self) -> Result<Json, LedgerError> {
        self.bump();
        let mut items = Vec::new();
        self.skip_ws();
        if self.peek() == Some(b']') {
            self.bump();
            return Ok(Json::Array(items));
        }
        loop {
            items.push(self.parse_value()?);
            self.skip_ws();
            match self.bump() {
                Some(b',') => {}
                Some(b']') => break,
                _ => return Err(LedgerError::Json("expected array delimiter".to_string())),
            }
        }
        Ok(Json::Array(items))
    }

    fn parse_object(&mut self) -> Result<Json, LedgerError> {
        self.bump();
        let mut fields = BTreeMap::new();
        self.skip_ws();
        if self.peek() == Some(b'}') {
            self.bump();
            return Ok(Json::Object(fields));
        }
        loop {
            self.skip_ws();
            let key = self.parse_string()?;
            self.skip_ws();
            if self.bump() != Some(b':') {
                return Err(LedgerError::Json("expected object colon".to_string()));
            }
            let value = self.parse_value()?;
            fields.insert(key, value);
            self.skip_ws();
            match self.bump() {
                Some(b',') => {}
                Some(b'}') => break,
                _ => return Err(LedgerError::Json("expected object delimiter".to_string())),
            }
        }
        Ok(Json::Object(fields))
    }

    fn parse_int(&mut self) -> Result<Json, LedgerError> {
        let start = self.pos;
        if self.peek() == Some(b'-') {
            self.bump();
        }
        match self.peek() {
            Some(b'0') => {
                self.bump();
                if matches!(self.peek(), Some(b'0'..=b'9')) {
                    return Err(LedgerError::Json("leading zero integer".to_string()));
                }
            }
            Some(b'1'..=b'9') => {
                while matches!(self.peek(), Some(b'0'..=b'9')) {
                    self.bump();
                }
            }
            _ => return Err(LedgerError::Json("invalid integer".to_string())),
        }
        if matches!(self.peek(), Some(b'.' | b'e' | b'E')) {
            return Err(LedgerError::Json("floats are not legal".to_string()));
        }
        let text = std::str::from_utf8(&self.input[start..self.pos])
            .map_err(|_| LedgerError::Json("invalid integer bytes".to_string()))?;
        text.parse::<i64>()
            .map(Json::Int)
            .map_err(|_| LedgerError::Json("integer outside i64".to_string()))
    }
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    let digest = sha256(bytes);
    let mut out = String::with_capacity(64);
    const HEX: &[u8; 16] = b"0123456789abcdef";
    for b in digest {
        out.push(HEX[(b >> 4) as usize] as char);
        out.push(HEX[(b & 0x0f) as usize] as char);
    }
    out
}

pub fn sha256(bytes: &[u8]) -> [u8; 32] {
    const H0: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];

    let bit_len = (bytes.len() as u64) * 8;
    let mut padded = bytes.to_vec();
    padded.push(0x80);
    while padded.len() % 64 != 56 {
        padded.push(0);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());

    let mut h = H0;
    for chunk in padded.chunks_exact(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            let j = i * 4;
            w[i] = u32::from_be_bytes([chunk[j], chunk[j + 1], chunk[j + 2], chunk[j + 3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }

        let mut a = h[0];
        let mut b = h[1];
        let mut c = h[2];
        let mut d = h[3];
        let mut e = h[4];
        let mut f = h[5];
        let mut g = h[6];
        let mut hh = h[7];

        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);

            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }

    let mut out = [0u8; 32];
    for (i, word) in h.iter().enumerate() {
        out[i * 4..i * 4 + 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

pub fn sha512(bytes: &[u8]) -> [u8; 64] {
    const H0: [u64; 8] = [
        0x6a09e667f3bcc908,
        0xbb67ae8584caa73b,
        0x3c6ef372fe94f82b,
        0xa54ff53a5f1d36f1,
        0x510e527fade682d1,
        0x9b05688c2b3e6c1f,
        0x1f83d9abfb41bd6b,
        0x5be0cd19137e2179,
    ];
    const K: [u64; 80] = [
        0x428a2f98d728ae22,
        0x7137449123ef65cd,
        0xb5c0fbcfec4d3b2f,
        0xe9b5dba58189dbbc,
        0x3956c25bf348b538,
        0x59f111f1b605d019,
        0x923f82a4af194f9b,
        0xab1c5ed5da6d8118,
        0xd807aa98a3030242,
        0x12835b0145706fbe,
        0x243185be4ee4b28c,
        0x550c7dc3d5ffb4e2,
        0x72be5d74f27b896f,
        0x80deb1fe3b1696b1,
        0x9bdc06a725c71235,
        0xc19bf174cf692694,
        0xe49b69c19ef14ad2,
        0xefbe4786384f25e3,
        0x0fc19dc68b8cd5b5,
        0x240ca1cc77ac9c65,
        0x2de92c6f592b0275,
        0x4a7484aa6ea6e483,
        0x5cb0a9dcbd41fbd4,
        0x76f988da831153b5,
        0x983e5152ee66dfab,
        0xa831c66d2db43210,
        0xb00327c898fb213f,
        0xbf597fc7beef0ee4,
        0xc6e00bf33da88fc2,
        0xd5a79147930aa725,
        0x06ca6351e003826f,
        0x142929670a0e6e70,
        0x27b70a8546d22ffc,
        0x2e1b21385c26c926,
        0x4d2c6dfc5ac42aed,
        0x53380d139d95b3df,
        0x650a73548baf63de,
        0x766a0abb3c77b2a8,
        0x81c2c92e47edaee6,
        0x92722c851482353b,
        0xa2bfe8a14cf10364,
        0xa81a664bbc423001,
        0xc24b8b70d0f89791,
        0xc76c51a30654be30,
        0xd192e819d6ef5218,
        0xd69906245565a910,
        0xf40e35855771202a,
        0x106aa07032bbd1b8,
        0x19a4c116b8d2d0c8,
        0x1e376c085141ab53,
        0x2748774cdf8eeb99,
        0x34b0bcb5e19b48a8,
        0x391c0cb3c5c95a63,
        0x4ed8aa4ae3418acb,
        0x5b9cca4f7763e373,
        0x682e6ff3d6b2b8a3,
        0x748f82ee5defb2fc,
        0x78a5636f43172f60,
        0x84c87814a1f0ab72,
        0x8cc702081a6439ec,
        0x90befffa23631e28,
        0xa4506cebde82bde9,
        0xbef9a3f7b2c67915,
        0xc67178f2e372532b,
        0xca273eceea26619c,
        0xd186b8c721c0c207,
        0xeada7dd6cde0eb1e,
        0xf57d4f7fee6ed178,
        0x06f067aa72176fba,
        0x0a637dc5a2c898a6,
        0x113f9804bef90dae,
        0x1b710b35131c471b,
        0x28db77f523047d84,
        0x32caab7b40c72493,
        0x3c9ebe0a15c9bebc,
        0x431d67c49c100d4c,
        0x4cc5d4becb3e42b6,
        0x597f299cfc657e2a,
        0x5fcb6fab3ad6faec,
        0x6c44198c4a475817,
    ];

    let bit_len = (bytes.len() as u128) * 8;
    let mut padded = bytes.to_vec();
    padded.push(0x80);
    while padded.len() % 128 != 112 {
        padded.push(0);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());

    let mut h = H0;
    for chunk in padded.chunks_exact(128) {
        let mut w = [0u64; 80];
        for i in 0..16 {
            let j = i * 8;
            w[i] = u64::from_be_bytes([
                chunk[j],
                chunk[j + 1],
                chunk[j + 2],
                chunk[j + 3],
                chunk[j + 4],
                chunk[j + 5],
                chunk[j + 6],
                chunk[j + 7],
            ]);
        }
        for i in 16..80 {
            let s0 = w[i - 15].rotate_right(1) ^ w[i - 15].rotate_right(8) ^ (w[i - 15] >> 7);
            let s1 = w[i - 2].rotate_right(19) ^ w[i - 2].rotate_right(61) ^ (w[i - 2] >> 6);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }

        let mut a = h[0];
        let mut b = h[1];
        let mut c = h[2];
        let mut d = h[3];
        let mut e = h[4];
        let mut f = h[5];
        let mut g = h[6];
        let mut hh = h[7];

        for i in 0..80 {
            let s1 = e.rotate_right(14) ^ e.rotate_right(18) ^ e.rotate_right(41);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(28) ^ a.rotate_right(34) ^ a.rotate_right(39);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);

            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }

    let mut out = [0u8; 64];
    for (i, word) in h.iter().enumerate() {
        out[i * 8..i * 8 + 8].copy_from_slice(&word.to_be_bytes());
    }
    out
}

impl Event {
    fn from_value(value: Json) -> Self {
        let canonical = canonical_json(&value);
        let id = format!("sha256:{}", sha256_hex(canonical.as_bytes()));
        Self {
            id,
            value,
            canonical,
        }
    }
}

impl Ledger {
    pub fn empty() -> Self {
        Self {
            events: BTreeMap::new(),
        }
    }

    pub fn parse_jsonl(input: &str) -> Result<Self, LedgerError> {
        let mut ledger = Self::empty();
        for line in input.lines() {
            if line.trim().is_empty() {
                continue;
            }
            let value = parse_json(line)?;
            ledger.insert(Event::from_value(value))?;
        }
        Ok(ledger)
    }

    pub fn merge(&self, other: &Self) -> Result<Self, LedgerError> {
        let mut out = self.clone();
        for event in other.events.values() {
            out.insert(event.clone())?;
        }
        Ok(out)
    }

    fn insert(&mut self, event: Event) -> Result<(), LedgerError> {
        if let Some(existing) = self.events.get(&event.id) {
            if existing.canonical != event.canonical {
                return Err(LedgerError::ContentAddressViolation(event.id));
            }
        } else {
            self.events.insert(event.id.clone(), event);
        }
        Ok(())
    }

    pub fn to_canonical_jsonl(&self) -> String {
        let mut out = String::new();
        for event in self.events.values() {
            out.push_str(&event.canonical);
            out.push('\n');
        }
        out
    }

    pub(crate) fn event_values(&self) -> impl Iterator<Item = &Event> {
        self.events.values()
    }

    pub fn fold(&self) -> Json {
        let accounts = self.accounts();
        accounts_to_json(&accounts)
    }

    pub fn audit_codes(&self) -> Vec<String> {
        let (registers, account_info) = self.resolve_registers();
        let accounts = self.accounts_from_info(&account_info);
        let mut codes = BTreeSet::new();

        for account in &accounts {
            let key_subject = canonical_json(&json_string_array(&account.key));
            if account.granted_lease_mbits > account.ceiling_mbits {
                codes.insert(format!("I1 {}", key_subject));
            }
            if account.cumulative_mbits > account.ceiling_mbits {
                codes.insert(format!("I2 {}", key_subject));
            }
        }

        for (key, info) in &registers {
            let no_well_formed = !account_info.contains_key(key);
            if info.has_malformed || no_well_formed || info.conflicted {
                codes.insert(format!("I7 {}", canonical_json(&json_string_array(key))));
            }
        }

        // A register whose key cannot parse forms no account — but it is
        // CONVICTED (I7, subject = canonical JSON of the raw key value),
        // never silently neutralized (SPEC I7 arm, 2026-07-06).
        for event in self.events.values() {
            if kind(&event.value) == Some("register")
                && as_key(obj_get(&event.value, "key")).is_none()
            {
                let raw = match obj_get(&event.value, "key") {
                    Some(v) => canonical_json(v),
                    None => "null".to_string(),
                };
                codes.insert(format!("I7 {raw}"));
            }
        }

        let leases = self.lease_index();
        for lease in leases.values() {
            let key = as_key(obj_get(&lease.value, "key"));
            let subject = lease.id.clone();
            match key {
                Some(ref key) => match account_info.get(key) {
                    Some(info) => {
                        let issuer = as_string(obj_get(&lease.value, "issuer"));
                        if issuer.map_or(true, |issuer| !info.issuers.contains(issuer)) {
                            codes.insert(format!("I5 {}", subject));
                        }
                    }
                    None => {
                        codes.insert(format!("I5 {}", subject));
                    }
                },
                None => {
                    codes.insert(format!("I5 {}", subject));
                }
            }
        }

        let mut debits_by_lease: BTreeMap<String, i64> = BTreeMap::new();
        let mut charge_slots: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();

        for charge in self
            .events
            .values()
            .filter(|event| kind(&event.value) == Some("charge"))
        {
            let id = charge.id.clone();
            if charge_i6(&charge.value) {
                codes.insert(format!("I6 {}", id));
            }

            let lease_id = as_string(obj_get(&charge.value, "lease_id")).unwrap_or("");
            let maybe_lease = leases.get(lease_id);
            if let Some(lease) = maybe_lease {
                let charge_key = as_key(obj_get(&charge.value, "key"));
                let lease_key = as_key(obj_get(&lease.value, "key"));
                let charge_node = as_string(obj_get(&charge.value, "node"));
                let lease_node = as_string(obj_get(&lease.value, "node"));
                let charge_tick = as_int(obj_get(&charge.value, "tick"));
                let lease_expires = as_int(obj_get(&lease.value, "expires_tick"));

                let key_mismatch =
                    charge_key.is_none() || lease_key.is_none() || charge_key != lease_key;
                let node_mismatch =
                    charge_node.is_none() || lease_node.is_none() || charge_node != lease_node;
                let expired = match (charge_tick, lease_expires) {
                    (Some(tick), Some(expires)) => tick > expires,
                    _ => false,
                };
                if key_mismatch || node_mismatch || expired {
                    codes.insert(format!("I4 {}", id));
                }
                if let Some(debit) = as_uint(obj_get(&charge.value, "debit_mbits")) {
                    *debits_by_lease.entry(lease_id.to_string()).or_insert(0) += debit;
                }
            } else {
                codes.insert(format!("I4 {}", id));
            }

            if let Some(seq) = as_uint(obj_get(&charge.value, "charge_seq")) {
                let node = as_string(obj_get(&charge.value, "node")).unwrap_or("");
                let slot = Json::Array(vec![
                    Json::String(node.to_string()),
                    Json::String(lease_id.to_string()),
                    Json::Int(seq),
                ]);
                charge_slots
                    .entry(canonical_json(&slot))
                    .or_default()
                    .insert(id);
            }
        }

        for lease in leases.values() {
            if let Some(amount) = as_uint(obj_get(&lease.value, "amount_mbits")) {
                if debits_by_lease.get(&lease.id).copied().unwrap_or(0) > amount {
                    codes.insert(format!("I3 {}", lease.id));
                }
            }
        }

        for (slot, ids) in charge_slots {
            if ids.len() > 1 {
                codes.insert(format!("I8 {}", slot));
            }
        }

        codes.into_iter().collect()
    }

    fn accounts(&self) -> Vec<Account> {
        let (_, infos) = self.resolve_registers();
        self.accounts_from_info(&infos)
    }

    fn accounts_from_info(&self, infos: &BTreeMap<Vec<String>, AccountInfo>) -> Vec<Account> {
        let mut accounts = Vec::new();
        for (key, info) in infos {
            let mut cumulative_mbits = 0;
            let mut demanded_mbits = 0;
            let mut granted_lease_mbits = 0;
            for event in self.events.values() {
                match kind(&event.value) {
                    Some("charge") => {
                        if as_key(obj_get(&event.value, "key")).as_ref() == Some(key) {
                            if let Some(debit) = as_uint(obj_get(&event.value, "debit_mbits")) {
                                cumulative_mbits += debit;
                            }
                            if let Some(demand) = as_uint(obj_get(&event.value, "demand_mbits")) {
                                demanded_mbits += demand;
                            }
                        }
                    }
                    Some("lease") => {
                        if as_key(obj_get(&event.value, "key")).as_ref() == Some(key) {
                            if let Some(amount) = as_uint(obj_get(&event.value, "amount_mbits")) {
                                granted_lease_mbits += amount;
                            }
                        }
                    }
                    _ => {}
                }
            }
            accounts.push(Account {
                key: key.clone(),
                subject_entropy_mbits: info.entropy,
                ceiling_mbits: info.ceiling,
                cumulative_mbits,
                demanded_mbits,
                granted_lease_mbits,
                leakage_class: leakage_class(cumulative_mbits, info.entropy).to_string(),
                incident: demanded_mbits * 1000 >= 800 * info.entropy,
                conflicted: info.conflicted,
            });
        }
        accounts.sort_by_key(|account| canonical_json(&json_string_array(&account.key)));
        accounts
    }

    fn resolve_registers(
        &self,
    ) -> (
        BTreeMap<Vec<String>, RegisterGroup>,
        BTreeMap<Vec<String>, AccountInfo>,
    ) {
        let mut groups: BTreeMap<Vec<String>, RegisterGroup> = BTreeMap::new();
        for event in self.events.values() {
            if kind(&event.value) != Some("register") {
                continue;
            }
            let key = match as_key(obj_get(&event.value, "key")) {
                Some(key) => key,
                // Unparseable key (missing, non-list, non-string elements):
                // forms NO group — aliasing it to the empty key would let a
                // junk register form a phantom account and diverge from the
                // reference. Convicted I7 in audit_codes with the raw key
                // value as subject (SPEC I7, amended 2026-07-06).
                None => continue,
            };
            let entry = groups.entry(key).or_default();
            let entropy = as_int(obj_get(&event.value, "subject_entropy_mbits"));
            let ceiling = as_uint(obj_get(&event.value, "ceiling_mbits"));
            let well_formed = entropy.map_or(false, |n| n > 0) && ceiling.is_some();
            if well_formed {
                let entropy = entropy.unwrap();
                let ceiling = ceiling.unwrap();
                if entry.well_formed_canonicals.insert(event.canonical.clone()) {
                    if entry.well_formed_canonicals.len() > 1 {
                        entry.conflicted = true;
                    }
                }
                entry.min_entropy = Some(entry.min_entropy.map_or(entropy, |n| n.min(entropy)));
                entry.min_ceiling = Some(entry.min_ceiling.map_or(ceiling, |n| n.min(ceiling)));
                if let Some(issuer) = as_string(obj_get(&event.value, "issuer")) {
                    entry.issuers.insert(issuer.to_string());
                }
            } else {
                entry.has_malformed = true;
            }
        }

        let mut infos = BTreeMap::new();
        for (key, group) in &groups {
            if let (Some(entropy), Some(ceiling)) = (group.min_entropy, group.min_ceiling) {
                infos.insert(
                    key.clone(),
                    AccountInfo {
                        entropy,
                        ceiling,
                        issuers: group.issuers.clone(),
                        conflicted: group.conflicted || group.has_malformed,
                    },
                );
            }
        }
        (groups, infos)
    }

    fn lease_index(&self) -> BTreeMap<String, Event> {
        let mut leases = BTreeMap::new();
        for event in self.events.values() {
            if kind(&event.value) == Some("lease") {
                leases.insert(event.id.clone(), event.clone());
            }
        }
        leases
    }
}

#[derive(Default, Debug, Clone)]
struct RegisterGroup {
    has_malformed: bool,
    conflicted: bool,
    min_entropy: Option<i64>,
    min_ceiling: Option<i64>,
    issuers: BTreeSet<String>,
    well_formed_canonicals: BTreeSet<String>,
}

#[derive(Debug, Clone)]
struct AccountInfo {
    entropy: i64,
    ceiling: i64,
    issuers: BTreeSet<String>,
    conflicted: bool,
}

fn accounts_to_json(accounts: &[Account]) -> Json {
    let mut account_values = Vec::with_capacity(accounts.len());
    for account in accounts {
        let mut obj = BTreeMap::new();
        obj.insert(
            "ceiling_mbits".to_string(),
            Json::Int(account.ceiling_mbits),
        );
        obj.insert("conflicted".to_string(), Json::Bool(account.conflicted));
        obj.insert(
            "cumulative_mbits".to_string(),
            Json::Int(account.cumulative_mbits),
        );
        obj.insert(
            "demanded_mbits".to_string(),
            Json::Int(account.demanded_mbits),
        );
        obj.insert(
            "granted_lease_mbits".to_string(),
            Json::Int(account.granted_lease_mbits),
        );
        obj.insert("incident".to_string(), Json::Bool(account.incident));
        obj.insert("key".to_string(), json_string_array(&account.key));
        obj.insert(
            "leakage_class".to_string(),
            Json::String(account.leakage_class.clone()),
        );
        obj.insert(
            "subject_entropy_mbits".to_string(),
            Json::Int(account.subject_entropy_mbits),
        );
        account_values.push(Json::Object(obj));
    }
    let mut root = BTreeMap::new();
    root.insert("accounts".to_string(), Json::Array(account_values));
    Json::Object(root)
}

fn leakage_class(cumulative_mbits: i64, subject_entropy_mbits: i64) -> &'static str {
    let c = cumulative_mbits.min(subject_entropy_mbits);
    let s = subject_entropy_mbits;
    if c * 1000 <= 50 * s {
        "negligible"
    } else if c * 1000 <= 250 * s {
        "bounded"
    } else if c * 1000 <= 500 * s {
        "material"
    } else if c * 1000 <= 800 * s {
        "unsafe"
    } else {
        "reconstructed"
    }
}

fn charge_i6(value: &Json) -> bool {
    let demand = as_uint(obj_get(value, "demand_mbits"));
    let debit = as_uint(obj_get(value, "debit_mbits"));
    let estimate = as_uint(obj_get(value, "estimate_total_mbits"));
    let seq = as_uint(obj_get(value, "charge_seq"));
    let reason = as_string(obj_get(value, "reason_class"));

    if demand.is_none() || debit.is_none() || estimate.is_none() {
        return true;
    }
    if seq.map_or(true, |n| n < 1) {
        return true;
    }
    let reason = match reason {
        Some(r)
            if matches!(
                r,
                "EMITTED"
                    | "REFUSED_ESTIMATOR"
                    | "REFUSED_BLOCKED"
                    | "REFUSED_CEILING"
                    | "REFUSED_COUPLED"
            ) =>
        {
            r
        }
        _ => return true,
    };

    let t = estimate.unwrap();
    let demand = demand.unwrap();
    let debit = debit.unwrap();
    let accepted_is_true = as_bool(obj_get(value, "accepted")) == Some(true);
    if accepted_is_true != (reason == "EMITTED") {
        return true;
    }
    if debit != if reason == "EMITTED" { t } else { 0 } {
        return true;
    }
    if demand != if reason == "REFUSED_ESTIMATOR" { 0 } else { t } {
        return true;
    }
    false
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SettlementVersion {
    V1,
    V2,
}

impl SettlementVersion {
    pub fn spec_name(self) -> &'static str {
        match self {
            SettlementVersion::V1 => "charge-settlement/1",
            SettlementVersion::V2 => "charge-settlement/2",
        }
    }
}

#[derive(Debug, Clone, Default)]
struct SettlementState {
    accounts: BTreeMap<String, SettlementAccount>,
    escrows: BTreeMap<String, EscrowState>,
    bonds: BTreeMap<String, BondState>,
    deposited_total: i64,
}

#[derive(Debug, Clone, Default)]
struct SettlementAccount {
    deposited_ucr: i64,
    locked_out_ucr: i64,
    released_in_ucr: i64,
    refunded_in_ucr: i64,
    bonded_out_ucr: i64,
    bond_returned_in_ucr: i64,
    slashed_in_ucr: i64,
}

impl SettlementAccount {
    fn available(&self, version: SettlementVersion) -> i64 {
        let mut available =
            self.deposited_ucr + self.released_in_ucr + self.refunded_in_ucr - self.locked_out_ucr;
        if version == SettlementVersion::V2 {
            available += self.bond_returned_in_ucr + self.slashed_in_ucr - self.bonded_out_ucr;
        }
        available
    }
}

#[derive(Debug, Clone, Default)]
struct EscrowState {
    amount_ucr: i64,
    released_ucr: i64,
    refunded_ucr: i64,
}

impl EscrowState {
    fn remaining(&self) -> i64 {
        self.amount_ucr - self.released_ucr - self.refunded_ucr
    }
}

#[derive(Debug, Clone, Default)]
struct BondState {
    amount_ucr: i64,
    returned_ucr: i64,
    slashed_ucr: i64,
}

impl BondState {
    fn remaining(&self) -> i64 {
        self.amount_ucr - self.returned_ucr - self.slashed_ucr
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum DefaultDirection {
    Release,
    Refund,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum EvidenceLane {
    Attested,
    PlatformLog,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum Independence {
    Party,
    Operator,
    RoleSeparated,
    AdversarialReview,
}

#[derive(Debug, Clone, Copy)]
struct OutcomeSpec {
    lane: EvidenceLane,
    quorum: i64,
    min_independence: Independence,
    min_bond_ucr: i64,
    contest_ticks: i64,
}

impl Ledger {
    pub fn inferred_settlement_version(&self) -> SettlementVersion {
        for event in self.events.values() {
            match kind(&event.value) {
                Some("outcome_attestation") | Some("bond_resolution") => {
                    return SettlementVersion::V2
                }
                Some("escrow") if obj_get(&event.value, "outcome").is_some() => {
                    return SettlementVersion::V2
                }
                Some("release") | Some("default_resolution")
                    if obj_get(&event.value, "attestation_ids").is_some() =>
                {
                    return SettlementVersion::V2
                }
                _ => {}
            }
        }
        SettlementVersion::V1
    }

    pub fn settlement_fold_v1(&self) -> Json {
        settlement_to_json(
            &self.settlement_state(SettlementVersion::V1),
            SettlementVersion::V1,
        )
    }

    pub fn settlement_fold_v2(&self) -> Json {
        settlement_to_json(
            &self.settlement_state(SettlementVersion::V2),
            SettlementVersion::V2,
        )
    }

    pub fn settlement_fold_for_version(&self, version: SettlementVersion) -> Json {
        settlement_to_json(&self.settlement_state(version), version)
    }

    pub fn settlement_conservation_pair(&self, version: SettlementVersion) -> (i64, i64) {
        let state = self.settlement_state(version);
        let accounts = state
            .accounts
            .values()
            .map(|account| account.available(version))
            .sum::<i64>();
        let escrows = state
            .escrows
            .values()
            .map(EscrowState::remaining)
            .sum::<i64>();
        let bonds = if version == SettlementVersion::V2 {
            state.bonds.values().map(BondState::remaining).sum::<i64>()
        } else {
            0
        };
        (accounts + escrows + bonds, state.deposited_total)
    }

    pub fn settlement_conservation_json(&self, version: SettlementVersion) -> Json {
        let (left, right) = self.settlement_conservation_pair(version);
        Json::Array(vec![Json::Int(left), Json::Int(right)])
    }

    pub fn settlement_audit_codes(&self) -> Vec<String> {
        let state = self.settlement_state(SettlementVersion::V2);
        let escrows = self.escrow_index();
        let attestations = self.attestation_index();
        let information_codes = self.audit_codes();
        let mut codes = BTreeSet::new();

        for (account, info) in &state.accounts {
            if info.available(SettlementVersion::V2) < 0 {
                codes.insert(format!("S1 {account}"));
            }
        }

        for (escrow_id, escrow) in &state.escrows {
            if escrow.released_ucr + escrow.refunded_ucr > escrow.amount_ucr {
                codes.insert(format!("S2 {escrow_id}"));
            }
        }

        for (attestation_id, bond) in &state.bonds {
            if bond.returned_ucr + bond.slashed_ucr > bond.amount_ucr {
                codes.insert(format!("S10 {attestation_id}"));
            }
        }

        let mut identity_slots: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();

        for event in self.events.values() {
            let Some(k) = kind(&event.value) else {
                continue;
            };
            if !is_settlement_kind(k) {
                continue;
            }

            if settlement_s6(&event.value) {
                codes.insert(format!("S6 {}", event.id));
            }

            if let Some(slot) = settlement_identity_slot(&event.value) {
                identity_slots
                    .entry(slot)
                    .or_default()
                    .insert(event.id.clone());
            }

            match k {
                "release" => {
                    let escrow = as_string(obj_get(&event.value, "escrow_id"))
                        .and_then(|id| escrows.get(id));
                    if escrow.is_none() {
                        codes.insert(format!("S2 {}", event.id));
                    }
                    if self.release_receipts_fail(&event.value, escrow) {
                        codes.insert(format!("S3 {}", event.id));
                    }
                    if escrow.map_or(false, |escrow| {
                        self.clean_court_fail(&escrow.value, &information_codes)
                    }) {
                        codes.insert(format!("S4 {}", event.id));
                    }
                    if escrow.map_or(false, |escrow| expired_release(&event.value, &escrow.value)) {
                        codes.insert(format!("S7 {}", event.id));
                    }
                    if let Some(escrow) = escrow {
                        if obj_get(&escrow.value, "outcome").is_some()
                            && self.outcome_release_fails(
                                &event.value,
                                escrow,
                                &state,
                                OutcomeFailureCode::S9,
                            )
                        {
                            codes.insert(format!("S9 {}", event.id));
                        }
                    }
                }
                "refund" => {
                    if as_string(obj_get(&event.value, "escrow_id"))
                        .and_then(|id| escrows.get(id))
                        .is_none()
                    {
                        codes.insert(format!("S2 {}", event.id));
                    }
                }
                "default_resolution" => {
                    let escrow = as_string(obj_get(&event.value, "escrow_id"))
                        .and_then(|id| escrows.get(id));
                    let direction = escrow.and_then(|escrow| {
                        default_direction(&event.value, &escrow.value, SettlementVersion::V2)
                    });
                    if escrow.is_none() || direction.is_none() {
                        codes.insert(format!("S2 {}", event.id));
                    }
                    if escrow.map_or(false, |escrow| {
                        premature_default(&event.value, &escrow.value)
                    }) {
                        codes.insert(format!("S8 {}", event.id));
                    }
                    if let (Some(escrow), Some(DefaultDirection::Release)) = (escrow, direction) {
                        let release_checks_fail = self
                            .release_receipts_fail(&event.value, Some(escrow))
                            || self.clean_court_fail(&escrow.value, &information_codes);
                        let outcome_checks_fail = obj_get(&escrow.value, "outcome").is_some()
                            && self.outcome_release_fails(
                                &event.value,
                                escrow,
                                &state,
                                OutcomeFailureCode::S8,
                            );
                        if release_checks_fail || outcome_checks_fail {
                            codes.insert(format!("S8 {}", event.id));
                        }
                    }
                }
                "bond_resolution" => {
                    // NO S6 gate here — the reference (settlement.py) runs the
                    // whole S10 block regardless of S6, so an S6-malformed
                    // bond_resolution whose attestation reference does not
                    // resolve (including a junk non-string id) still convicts
                    // "S10 unknown attestation". Gating on !S6 silently
                    // dropped that conviction and diverged on the adversarial
                    // corpus (soup-unhashable-ids-total).
                    let attestation = as_string(obj_get(&event.value, "attestation_id"))
                        .and_then(|id| attestations.get(id));
                    match attestation {
                        None => {
                            codes.insert(format!("S10 {}", event.id));
                        }
                        Some(attestation) => {
                            match as_string(obj_get(&event.value, "direction")) {
                                Some("return_to_attestor") => {
                                    if self.premature_bond_return(&event.value, attestation)
                                        || self.strict_override_exists(attestation, &state)
                                    {
                                        codes.insert(format!("S10 {}", event.id));
                                    }
                                }
                                Some("slash") => {
                                    // G19: when the slash NAMES its override,
                                    // the naming binds — judge the cited
                                    // referent, never scan.
                                    let override_ok =
                                        if obj_get(&event.value, "override_attestation_id")
                                            .is_some()
                                        {
                                            self.named_override_ok(
                                                &event.value,
                                                attestation,
                                                &state,
                                            )
                                        } else {
                                            self.strict_override_exists(attestation, &state)
                                        };
                                    if !override_ok || self.slash_beneficiary(attestation).is_none()
                                    {
                                        codes.insert(format!("S10 {}", event.id));
                                    }
                                }
                                _ => {}
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        for (slot, ids) in identity_slots {
            if ids.len() > 1 {
                codes.insert(format!("S5 {slot}"));
            }
        }

        codes.into_iter().collect()
    }

    fn settlement_state(&self, version: SettlementVersion) -> SettlementState {
        let escrows = self.escrow_index();
        let attestations = self.attestation_index();
        let mut state = SettlementState::default();

        for event in self.events.values() {
            match kind(&event.value) {
                Some("deposit") => {
                    if let Some(account) = as_string(obj_get(&event.value, "account")) {
                        let amount = as_uint(obj_get(&event.value, "amount_ucr")).unwrap_or(0);
                        state
                            .accounts
                            .entry(account.to_string())
                            .or_default()
                            .deposited_ucr += amount;
                        state.deposited_total += amount;
                    }
                }
                Some("escrow") => {
                    // All-or-nothing (SPEC §2, as bonds below): the escrow's
                    // remainder exists ONLY when its lock debited a real
                    // (string) payer account. A non-string payer with a uint
                    // amount would otherwise mint `amount` into the
                    // conservation LHS with no offsetting locked_out — the
                    // fold must telescope on ANY soup. S6 convicts the
                    // malformed escrow.
                    let payer = as_string(obj_get(&event.value, "payer"));
                    let amount = if payer.is_some() {
                        as_uint(obj_get(&event.value, "amount_ucr")).unwrap_or(0)
                    } else {
                        0
                    };
                    state.escrows.insert(
                        event.id.clone(),
                        EscrowState {
                            amount_ucr: amount,
                            ..EscrowState::default()
                        },
                    );
                    if let Some(payer) = payer {
                        state
                            .accounts
                            .entry(payer.to_string())
                            .or_default()
                            .locked_out_ucr += amount;
                    }
                    if let Some(payee) = as_string(obj_get(&event.value, "payee")) {
                        state.accounts.entry(payee.to_string()).or_default();
                    }
                }
                Some("outcome_attestation") if version == SettlementVersion::V2 => {
                    let attestor = as_string(obj_get(&event.value, "attestor"));
                    let amount = if attestor.is_some() {
                        as_uint(obj_get(&event.value, "bond_ucr")).unwrap_or(0)
                    } else {
                        0
                    };
                    state.bonds.insert(
                        event.id.clone(),
                        BondState {
                            amount_ucr: amount,
                            ..BondState::default()
                        },
                    );
                    if let Some(attestor) = attestor {
                        state
                            .accounts
                            .entry(attestor.to_string())
                            .or_default()
                            .bonded_out_ucr += amount;
                    }
                }
                _ => {}
            }
        }

        for event in self.events.values() {
            match kind(&event.value) {
                Some("release") => {
                    if let Some(amount) = as_uint(obj_get(&event.value, "amount_ucr")) {
                        if let Some(escrow) = as_string(obj_get(&event.value, "escrow_id"))
                            .and_then(|id| escrows.get(id))
                        {
                            add_release_to_state(&mut state, escrow, amount);
                        }
                    }
                }
                Some("refund") => {
                    if let Some(amount) = as_uint(obj_get(&event.value, "amount_ucr")) {
                        if let Some(escrow) = as_string(obj_get(&event.value, "escrow_id"))
                            .and_then(|id| escrows.get(id))
                        {
                            add_refund_to_state(&mut state, escrow, amount);
                        }
                    }
                }
                Some("default_resolution") => {
                    if let Some(amount) = as_uint(obj_get(&event.value, "amount_ucr")) {
                        if let Some(escrow) = as_string(obj_get(&event.value, "escrow_id"))
                            .and_then(|id| escrows.get(id))
                        {
                            match default_direction(&event.value, &escrow.value, version) {
                                Some(DefaultDirection::Release) => {
                                    add_release_to_state(&mut state, escrow, amount)
                                }
                                Some(DefaultDirection::Refund) => {
                                    add_refund_to_state(&mut state, escrow, amount)
                                }
                                None => {}
                            }
                        }
                    }
                }
                Some("bond_resolution") if version == SettlementVersion::V2 => {
                    if let (Some(amount), Some(attestation_id), Some(direction)) = (
                        as_uint(obj_get(&event.value, "amount_ucr")),
                        as_string(obj_get(&event.value, "attestation_id")),
                        as_string(obj_get(&event.value, "direction")),
                    ) {
                        if let Some(attestation) = attestations.get(attestation_id) {
                            match direction {
                                "return_to_attestor" => {
                                    if let Some(attestor) =
                                        as_string(obj_get(&attestation.value, "attestor"))
                                    {
                                        if let Some(bond) = state.bonds.get_mut(attestation_id) {
                                            bond.returned_ucr += amount;
                                        }
                                        state
                                            .accounts
                                            .entry(attestor.to_string())
                                            .or_default()
                                            .bond_returned_in_ucr += amount;
                                    }
                                }
                                "slash" => {
                                    if let Some(beneficiary) = self.slash_beneficiary(attestation) {
                                        if let Some(bond) = state.bonds.get_mut(attestation_id) {
                                            bond.slashed_ucr += amount;
                                        }
                                        state
                                            .accounts
                                            .entry(beneficiary)
                                            .or_default()
                                            .slashed_in_ucr += amount;
                                    }
                                }
                                _ => {}
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        state
    }

    fn escrow_index(&self) -> BTreeMap<String, Event> {
        let mut escrows = BTreeMap::new();
        for event in self.events.values() {
            if kind(&event.value) == Some("escrow") {
                escrows.insert(event.id.clone(), event.clone());
            }
        }
        escrows
    }

    fn attestation_index(&self) -> BTreeMap<String, Event> {
        let mut attestations = BTreeMap::new();
        for event in self.events.values() {
            if kind(&event.value) == Some("outcome_attestation") {
                attestations.insert(event.id.clone(), event.clone());
            }
        }
        attestations
    }

    fn release_receipts_fail(&self, value: &Json, escrow: Option<&Event>) -> bool {
        let Some(Json::Array(ids)) = obj_get(value, "charge_ids") else {
            return true;
        };
        if ids.is_empty() {
            return true;
        }
        let charge_keys = escrow.and_then(|escrow| charge_keys(&escrow.value));
        for item in ids {
            let Json::String(id) = item else {
                return true;
            };
            let Some(charge) = self.events.get(id) else {
                return true;
            };
            if kind(&charge.value) != Some("charge") {
                return true;
            }
            if as_bool(obj_get(&charge.value, "accepted")) != Some(true) {
                return true;
            }
            if let Some(charge_keys) = &charge_keys {
                let Some(key) = as_key(obj_get(&charge.value, "key")) else {
                    return true;
                };
                if !charge_keys.contains(&key) {
                    return true;
                }
            }
        }
        false
    }

    fn clean_court_fail(&self, escrow: &Json, information_codes: &[String]) -> bool {
        if as_bool(obj_get(escrow, "required_clean")) != Some(true) {
            return false;
        }
        let Some(keys) = charge_keys(escrow) else {
            return false;
        };
        information_codes
            .iter()
            .any(|code| self.information_code_touches_keys(code, &keys))
    }

    fn information_code_touches_keys(&self, code: &str, keys: &BTreeSet<Vec<String>>) -> bool {
        let Some((prefix, subject)) = code.split_once(' ') else {
            return true;
        };
        match prefix {
            "I1" | "I2" | "I7" => keys
                .iter()
                .any(|key| subject == canonical_json(&json_string_array(key))),
            "I3" | "I5" => self
                .events
                .get(subject)
                .and_then(|event| as_key(obj_get(&event.value, "key")))
                .map_or(false, |key| keys.contains(&key)),
            "I4" | "I6" => self
                .events
                .get(subject)
                .and_then(|event| as_key(obj_get(&event.value, "key")))
                .map_or(false, |key| keys.contains(&key)),
            "I8" => parse_json(subject)
                .ok()
                .and_then(|value| match value {
                    Json::Array(items) if items.len() == 3 => match &items[1] {
                        Json::String(lease_id) => Some(lease_id.clone()),
                        _ => None,
                    },
                    _ => None,
                })
                .and_then(|lease_id| self.events.get(&lease_id).cloned())
                .and_then(|event| as_key(obj_get(&event.value, "key")))
                .map_or(false, |key| keys.contains(&key)),
            _ => true,
        }
    }

    fn outcome_release_fails(
        &self,
        value: &Json,
        escrow: &Event,
        state: &SettlementState,
        _code: OutcomeFailureCode,
    ) -> bool {
        let outcome = match outcome_condition(&escrow.value) {
            Some(outcome) => outcome,
            None => return true,
        };
        let Some(Json::Array(ids)) = obj_get(value, "attestation_ids") else {
            return true;
        };
        if ids.is_empty() {
            return true;
        }

        let mut surviving_attestors = BTreeSet::new();
        let release_tick = as_int(obj_get(value, "tick"));
        for item in ids {
            let Json::String(id) = item else {
                return true;
            };
            let Some(attestation) = self.events.get(id) else {
                return true;
            };
            if kind(&attestation.value) != Some("outcome_attestation") {
                return true;
            }
            if attestation_s6(&attestation.value) {
                return true;
            }
            if as_string(obj_get(&attestation.value, "escrow_id")) != Some(escrow.id.as_str()) {
                return true;
            }
            if as_string(obj_get(&attestation.value, "claim")) != Some("occurred") {
                return true;
            }
            if !self.attestation_meets_floor(attestation, escrow, &outcome, state) {
                return true;
            }
            if let (Some(release_tick), Some(attestation_tick)) =
                (release_tick, as_int(obj_get(&attestation.value, "tick")))
            {
                if release_tick <= attestation_tick.saturating_add(outcome.contest_ticks) {
                    return true;
                }
            }
            if self.contesting_attestation_exists(attestation, escrow, &outcome, state, false) {
                return true;
            }
            if let Some(attestor) = as_string(obj_get(&attestation.value, "attestor")) {
                surviving_attestors.insert(attestor.to_string());
            }
        }

        surviving_attestors.len() < outcome.quorum as usize
    }

    fn contesting_attestation_exists(
        &self,
        attestation: &Event,
        escrow: &Event,
        outcome: &OutcomeSpec,
        state: &SettlementState,
        strict_lane: bool,
    ) -> bool {
        for other in self.events.values() {
            if self.is_contesting_candidate(other, attestation, escrow, outcome, state, strict_lane)
            {
                return true;
            }
        }
        false
    }

    /// The single per-candidate predicate (SPEC §9 S10.4), shared by the
    /// scan and the G19 named-referent path so the two modes cannot drift:
    /// a well-formed attestation on the same escrow with the OPPOSITE
    /// claim, a lane above (strictly, for overrides) the contested one's,
    /// meeting the condition's floors.
    #[allow(clippy::too_many_arguments)]
    fn is_contesting_candidate(
        &self,
        other: &Event,
        attestation: &Event,
        escrow: &Event,
        outcome: &OutcomeSpec,
        state: &SettlementState,
        strict_lane: bool,
    ) -> bool {
        if kind(&other.value) != Some("outcome_attestation") || other.id == attestation.id {
            return false;
        }
        if attestation_s6(&other.value) {
            return false;
        }
        if as_string(obj_get(&other.value, "escrow_id")) != Some(escrow.id.as_str()) {
            return false;
        }
        let Some(lane) = as_string(obj_get(&attestation.value, "lane")).and_then(evidence_lane)
        else {
            return false;
        };
        let opposite = match as_string(obj_get(&attestation.value, "claim")) {
            Some("occurred") => "not_occurred",
            Some("not_occurred") => "occurred",
            _ => return false,
        };
        if as_string(obj_get(&other.value, "claim")) != Some(opposite) {
            return false;
        }
        let Some(other_lane) = as_string(obj_get(&other.value, "lane")).and_then(evidence_lane)
        else {
            return false;
        };
        let lane_ok = if strict_lane {
            other_lane > lane
        } else {
            other_lane >= lane
        };
        lane_ok && self.attestation_meets_floor(other, escrow, outcome, state)
    }

    /// G19 named mode (SPEC §9 S10.4): the slash carries
    /// `override_attestation_id` and is judged on EXACTLY that referent —
    /// present in the ledger and qualifying. A qualifying override that
    /// exists but was not the one named does not save the slash. Total on
    /// junk: a non-string name resolves to nothing and convicts.
    fn named_override_ok(
        &self,
        resolution: &Json,
        attestation: &Event,
        state: &SettlementState,
    ) -> bool {
        let Some(named) = as_string(obj_get(resolution, "override_attestation_id"))
            .and_then(|id| self.events.get(id))
        else {
            return false;
        };
        let Some(escrow_id) = as_string(obj_get(&attestation.value, "escrow_id")) else {
            return false;
        };
        let Some(escrow) = self.events.get(escrow_id) else {
            return false;
        };
        if kind(&escrow.value) != Some("escrow") {
            return false;
        }
        let Some(outcome) = outcome_condition(&escrow.value) else {
            return false;
        };
        self.is_contesting_candidate(named, attestation, escrow, &outcome, state, true)
    }

    fn attestation_meets_floor(
        &self,
        attestation: &Event,
        escrow: &Event,
        outcome: &OutcomeSpec,
        state: &SettlementState,
    ) -> bool {
        if attestation_s6(&attestation.value) {
            return false;
        }
        if as_string(obj_get(&attestation.value, "escrow_id")) != Some(escrow.id.as_str()) {
            return false;
        }
        let Some(lane) = as_string(obj_get(&attestation.value, "lane")).and_then(evidence_lane)
        else {
            return false;
        };
        if lane < outcome.lane {
            return false;
        }
        let Some(independence) = effective_independence(&attestation.value, &escrow.value) else {
            return false;
        };
        if independence < outcome.min_independence {
            return false;
        }
        if as_uint(obj_get(&attestation.value, "bond_ucr")).unwrap_or(-1) < outcome.min_bond_ucr {
            return false;
        }
        let Some(attestor) = as_string(obj_get(&attestation.value, "attestor")) else {
            return false;
        };
        state.accounts.get(attestor).map_or(false, |account| {
            account.available(SettlementVersion::V2) >= 0
        })
    }

    fn premature_bond_return(&self, resolution: &Json, attestation: &Event) -> bool {
        let Some(escrow_id) = as_string(obj_get(&attestation.value, "escrow_id")) else {
            return false;
        };
        let Some(escrow) = self.events.get(escrow_id) else {
            return false;
        };
        if kind(&escrow.value) != Some("escrow") {
            return false;
        }
        let Some(outcome) = outcome_condition(&escrow.value) else {
            return false;
        };
        match (
            as_int(obj_get(resolution, "tick")),
            as_int(obj_get(&attestation.value, "tick")),
        ) {
            (Some(resolution_tick), Some(attestation_tick)) => {
                resolution_tick <= attestation_tick.saturating_add(outcome.contest_ticks)
            }
            _ => false,
        }
    }

    fn strict_override_exists(&self, attestation: &Event, state: &SettlementState) -> bool {
        let Some(escrow_id) = as_string(obj_get(&attestation.value, "escrow_id")) else {
            return false;
        };
        let Some(escrow) = self.events.get(escrow_id) else {
            return false;
        };
        if kind(&escrow.value) != Some("escrow") {
            return false;
        }
        let Some(outcome) = outcome_condition(&escrow.value) else {
            return false;
        };
        self.contesting_attestation_exists(attestation, escrow, &outcome, state, true)
    }

    fn slash_beneficiary(&self, attestation: &Event) -> Option<String> {
        let escrow_id = as_string(obj_get(&attestation.value, "escrow_id"))?;
        let escrow = self.events.get(escrow_id)?;
        if kind(&escrow.value) != Some("escrow") {
            return None;
        }
        match as_string(obj_get(&attestation.value, "claim"))? {
            "occurred" => as_string(obj_get(&escrow.value, "payer")).map(str::to_string),
            "not_occurred" => as_string(obj_get(&escrow.value, "payee")).map(str::to_string),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Copy)]
enum OutcomeFailureCode {
    S8,
    S9,
}

fn settlement_to_json(state: &SettlementState, version: SettlementVersion) -> Json {
    let mut account_values = Vec::with_capacity(state.accounts.len());
    for (account, info) in &state.accounts {
        let mut obj = BTreeMap::new();
        obj.insert("account".to_string(), Json::String(account.clone()));
        obj.insert(
            "available_ucr".to_string(),
            Json::Int(info.available(version)),
        );
        if version == SettlementVersion::V2 {
            obj.insert(
                "bond_returned_in_ucr".to_string(),
                Json::Int(info.bond_returned_in_ucr),
            );
            obj.insert("bonded_out_ucr".to_string(), Json::Int(info.bonded_out_ucr));
        }
        obj.insert("deposited_ucr".to_string(), Json::Int(info.deposited_ucr));
        obj.insert("locked_out_ucr".to_string(), Json::Int(info.locked_out_ucr));
        obj.insert(
            "refunded_in_ucr".to_string(),
            Json::Int(info.refunded_in_ucr),
        );
        obj.insert(
            "released_in_ucr".to_string(),
            Json::Int(info.released_in_ucr),
        );
        if version == SettlementVersion::V2 {
            obj.insert("slashed_in_ucr".to_string(), Json::Int(info.slashed_in_ucr));
        }
        account_values.push(Json::Object(obj));
    }

    let mut escrow_values = Vec::with_capacity(state.escrows.len());
    for (escrow_id, escrow) in &state.escrows {
        let mut obj = BTreeMap::new();
        obj.insert("amount_ucr".to_string(), Json::Int(escrow.amount_ucr));
        obj.insert("escrow_id".to_string(), Json::String(escrow_id.clone()));
        obj.insert("refunded_ucr".to_string(), Json::Int(escrow.refunded_ucr));
        obj.insert("released_ucr".to_string(), Json::Int(escrow.released_ucr));
        obj.insert("remaining_ucr".to_string(), Json::Int(escrow.remaining()));
        escrow_values.push(Json::Object(obj));
    }

    let mut root = BTreeMap::new();
    root.insert("accounts".to_string(), Json::Array(account_values));
    if version == SettlementVersion::V2 {
        let mut bond_values = Vec::with_capacity(state.bonds.len());
        for (attestation_id, bond) in &state.bonds {
            let mut obj = BTreeMap::new();
            obj.insert("amount_ucr".to_string(), Json::Int(bond.amount_ucr));
            obj.insert(
                "attestation_id".to_string(),
                Json::String(attestation_id.clone()),
            );
            obj.insert("remaining_ucr".to_string(), Json::Int(bond.remaining()));
            obj.insert("returned_ucr".to_string(), Json::Int(bond.returned_ucr));
            obj.insert("slashed_ucr".to_string(), Json::Int(bond.slashed_ucr));
            bond_values.push(Json::Object(obj));
        }
        root.insert("bonds".to_string(), Json::Array(bond_values));
    }
    root.insert("escrows".to_string(), Json::Array(escrow_values));
    Json::Object(root)
}

fn add_release_to_state(state: &mut SettlementState, escrow: &Event, amount: i64) {
    // All-or-nothing (SPEC §2): the disbursement counts against the escrow
    // ONLY when it credits a real (string) destination account — else it
    // would drop the escrow remainder with no offsetting account gain and
    // break conservation (the mirror of the escrow-lock case). A
    // disbursement to a non-string party is convicted by S3/S2.
    if let Some(payee) = as_string(obj_get(&escrow.value, "payee")) {
        if let Some(info) = state.escrows.get_mut(&escrow.id) {
            info.released_ucr += amount;
        }
        state
            .accounts
            .entry(payee.to_string())
            .or_default()
            .released_in_ucr += amount;
    }
}

fn add_refund_to_state(state: &mut SettlementState, escrow: &Event, amount: i64) {
    // All-or-nothing: mirror of add_release_to_state, refund direction.
    if let Some(payer) = as_string(obj_get(&escrow.value, "payer")) {
        if let Some(info) = state.escrows.get_mut(&escrow.id) {
            info.refunded_ucr += amount;
        }
        state
            .accounts
            .entry(payer.to_string())
            .or_default()
            .refunded_in_ucr += amount;
    }
}

fn default_direction(
    resolution: &Json,
    escrow: &Json,
    version: SettlementVersion,
) -> Option<DefaultDirection> {
    if version == SettlementVersion::V2 && obj_get(escrow, "outcome").is_some() {
        return if non_empty_array(obj_get(resolution, "attestation_ids")) {
            Some(DefaultDirection::Release)
        } else {
            Some(DefaultDirection::Refund)
        };
    }
    match as_string(obj_get(escrow, "default_on_expiry")) {
        Some("release_to_payee") => Some(DefaultDirection::Release),
        Some("refund_to_payer") => Some(DefaultDirection::Refund),
        _ => None,
    }
}

fn non_empty_array(value: Option<&Json>) -> bool {
    matches!(value, Some(Json::Array(items)) if !items.is_empty())
}

fn expired_release(release: &Json, escrow: &Json) -> bool {
    match (
        as_int(obj_get(release, "tick")),
        as_int(obj_get(escrow, "expires_tick")),
    ) {
        (Some(tick), Some(expires)) => tick > expires,
        _ => false,
    }
}

fn premature_default(resolution: &Json, escrow: &Json) -> bool {
    match (
        as_int(obj_get(resolution, "tick")),
        as_int(obj_get(escrow, "expires_tick")),
    ) {
        (Some(tick), Some(expires)) => tick <= expires,
        _ => false,
    }
}

fn is_settlement_kind(kind: &str) -> bool {
    matches!(
        kind,
        "deposit"
            | "escrow"
            | "release"
            | "refund"
            | "default_resolution"
            | "outcome_attestation"
            | "bond_resolution"
    )
}

fn settlement_identity_slot(value: &Json) -> Option<String> {
    let k = kind(value)?;
    let actor_field = match k {
        "deposit" | "escrow" | "release" | "refund" => "issuer",
        "default_resolution" | "bond_resolution" => "submitter",
        "outcome_attestation" => "attestor",
        _ => return None,
    };
    let actor = as_string(obj_get(value, actor_field))?;
    let seq = as_uint(obj_get(value, "seq"))?;
    let slot = Json::Array(vec![
        Json::String(actor.to_string()),
        Json::String(k.to_string()),
        Json::Int(seq),
    ]);
    Some(canonical_json(&slot))
}

fn settlement_s6(value: &Json) -> bool {
    let Some(k) = kind(value) else {
        return false;
    };
    match k {
        "deposit" => amount_ucr_bad(value) || seq_bad(value),
        "escrow" => {
            amount_ucr_bad(value)
                || seq_bad(value)
                || charge_keys(value).is_none()
                // SPEC §3 S6: non-string payer/payee — the paired-quantity
                // all-or-nothing law's conviction arm (fable review F1).
                || as_string(obj_get(value, "payer")).is_none()
                || as_string(obj_get(value, "payee")).is_none()
                || !matches!(
                    as_string(obj_get(value, "default_on_expiry")),
                    Some("release_to_payee" | "refund_to_payer")
                )
                || escrow_outcome_s6(value)
        }
        "release" | "refund" | "default_resolution" => {
            amount_ucr_bad(value)
                || seq_bad(value)
                || as_string(obj_get(value, "escrow_id")).is_none()
        }
        "outcome_attestation" => attestation_s6(value),
        "bond_resolution" => bond_resolution_s6(value),
        _ => false,
    }
}

fn amount_ucr_bad(value: &Json) -> bool {
    as_uint(obj_get(value, "amount_ucr")).is_none()
}

fn seq_bad(value: &Json) -> bool {
    as_uint(obj_get(value, "seq")).map_or(true, |seq| seq < 1)
}

fn charge_keys(value: &Json) -> Option<BTreeSet<Vec<String>>> {
    let Json::Array(items) = obj_get(value, "charge_keys")? else {
        return None;
    };
    if items.is_empty() {
        return None;
    }
    let mut out = BTreeSet::new();
    for item in items {
        let key = as_key(Some(item))?;
        out.insert(key);
    }
    Some(out)
}

fn escrow_outcome_s6(value: &Json) -> bool {
    if obj_get(value, "outcome").is_none() {
        return false;
    }
    outcome_object(value).is_none()
        || as_string(obj_get(value, "default_on_expiry")) != Some("refund_to_payer")
}

fn outcome_condition(value: &Json) -> Option<OutcomeSpec> {
    if as_string(obj_get(value, "default_on_expiry")) != Some("refund_to_payer") {
        return None;
    }
    outcome_object(value)
}

fn outcome_object(value: &Json) -> Option<OutcomeSpec> {
    let Json::Object(fields) = obj_get(value, "outcome")? else {
        return None;
    };
    let metric = fields.get("metric");
    if !matches!(metric, Some(Json::String(_))) {
        return None;
    }
    let lane = as_string(fields.get("lane")).and_then(evidence_lane)?;
    let quorum = as_uint(fields.get("quorum"))?;
    if quorum < 1 {
        return None;
    }
    let min_independence = as_string(fields.get("min_independence")).and_then(independence)?;
    let min_bond_ucr = as_uint(fields.get("min_bond_ucr"))?;
    let contest_ticks = as_uint(fields.get("contest_ticks"))?;
    Some(OutcomeSpec {
        lane,
        quorum,
        min_independence,
        min_bond_ucr,
        contest_ticks,
    })
}

fn attestation_s6(value: &Json) -> bool {
    if as_string(obj_get(value, "escrow_id")).is_none()
        || as_string(obj_get(value, "attestor")).is_none()
        || as_string(obj_get(value, "independence")).is_none()
        || as_string(obj_get(value, "evidence")).is_none()
        || as_uint(obj_get(value, "bond_ucr")).is_none()
        || seq_bad(value)
    {
        return true;
    }
    if !matches!(
        as_string(obj_get(value, "claim")),
        Some("occurred" | "not_occurred")
    ) {
        return true;
    }
    if as_string(obj_get(value, "lane"))
        .and_then(evidence_lane)
        .is_none()
    {
        return true;
    }
    false
}

fn bond_resolution_s6(value: &Json) -> bool {
    as_string(obj_get(value, "attestation_id")).is_none()
        || as_string(obj_get(value, "submitter")).is_none()
        || !matches!(
            as_string(obj_get(value, "direction")),
            Some("return_to_attestor" | "slash")
        )
        || as_uint(obj_get(value, "amount_ucr")).is_none()
        || seq_bad(value)
}

fn evidence_lane(value: &str) -> Option<EvidenceLane> {
    match value {
        "attested" => Some(EvidenceLane::Attested),
        "platform_log" => Some(EvidenceLane::PlatformLog),
        _ => None,
    }
}

fn independence(value: &str) -> Option<Independence> {
    match value {
        "party" => Some(Independence::Party),
        "operator" => Some(Independence::Operator),
        "role_separated" => Some(Independence::RoleSeparated),
        "adversarial_review" => Some(Independence::AdversarialReview),
        _ => None,
    }
}

fn effective_independence(attestation: &Json, escrow: &Json) -> Option<Independence> {
    let declared = as_string(obj_get(attestation, "independence")).and_then(independence)?;
    let attestor = as_string(obj_get(attestation, "attestor"))?;
    if as_string(obj_get(escrow, "payer")) == Some(attestor)
        || as_string(obj_get(escrow, "payee")) == Some(attestor)
    {
        Some(Independence::Party)
    } else {
        Some(declared)
    }
}

// ---------------------------------------------------------------------------
// charge-views/1 — interpretation out of the timeless fold (VIEWS-SPEC.md)
//
// A view is a PURE function (fold, policy) -> report | refusal. The fold's
// embedded leakage_class/incident are the legacy-default view (the §V.5
// parity law); this port must reproduce views_traces/ bit-for-bit AND the
// embedded labels of every ledger_traces fold under the default policy.
// All-or-nothing: a malformed policy (W1) or fold input (W2) refuses the
// ENTIRE view. Integer cross-multiplication only; no floats.
// ---------------------------------------------------------------------------

const VIEWS_SPEC: &str = "charge-views/1";

fn views_policy_field_set_exact(policy: &BTreeMap<String, Json>) -> bool {
    const FIELDS: [&str; 6] = [
        "classes",
        "domains",
        "incident_permille",
        "name",
        "spec",
        "terminal_label",
    ];
    policy.len() == FIELDS.len() && FIELDS.iter().all(|f| policy.contains_key(*f))
}

/// VIEWS-SPEC §V.2 admissibility. Any failure refuses the whole view (W1).
pub fn views_policy_admissible(policy: &Json) -> bool {
    let fields = match policy {
        Json::Object(fields) => fields,
        _ => return false,
    };
    if !views_policy_field_set_exact(fields) {
        return false;
    }
    if as_string(fields.get("spec")) != Some(VIEWS_SPEC) {
        return false;
    }
    match as_string(fields.get("name")) {
        Some(name) if !name.is_empty() => {}
        _ => return false,
    }
    match fields.get("domains") {
        Some(Json::Null) => {}
        Some(Json::Array(prefixes)) => {
            if prefixes.is_empty() {
                return false;
            }
            for prefix in prefixes {
                match as_key(Some(prefix)) {
                    Some(parts) if !parts.is_empty() => {}
                    _ => return false,
                }
            }
        }
        _ => return false,
    }
    let classes = match fields.get("classes") {
        Some(Json::Array(classes)) if !classes.is_empty() => classes,
        _ => return false,
    };
    let mut labels: Vec<&str> = Vec::with_capacity(classes.len() + 1);
    let mut prev: Option<i64> = None;
    for class in classes {
        let class_fields = match class {
            Json::Object(class_fields) => class_fields,
            _ => return false,
        };
        if class_fields.len() != 2
            || !class_fields.contains_key("label")
            || !class_fields.contains_key("max_permille")
        {
            return false;
        }
        let label = match as_string(class_fields.get("label")) {
            Some(label) if !label.is_empty() => label,
            _ => return false,
        };
        let max_permille = match as_uint(class_fields.get("max_permille")) {
            Some(n) => n,
            None => return false,
        };
        if let Some(p) = prev {
            if max_permille <= p {
                return false; // strictly increasing: monotonicity is structural
            }
        }
        prev = Some(max_permille);
        labels.push(label);
    }
    let terminal = match as_string(fields.get("terminal_label")) {
        Some(terminal) if !terminal.is_empty() => terminal,
        _ => return false,
    };
    labels.push(terminal);
    let distinct: BTreeSet<&str> = labels.iter().copied().collect();
    if distinct.len() != labels.len() || distinct.contains("void") {
        return false; // "void" is reserved output vocabulary (§V.4)
    }
    as_uint(fields.get("incident_permille")).is_some()
}

struct ViewsAccountRow {
    key: Vec<String>,
    cumulative_mbits: i64,
    demanded_mbits: i64,
    subject_entropy_mbits: i64,
}

/// VIEWS-SPEC §V.3 input well-formedness. None -> refuse whole view (W2).
fn views_fold_accounts(fold: &Json) -> Option<Vec<ViewsAccountRow>> {
    let accounts = match obj_get(fold, "accounts") {
        Some(Json::Array(accounts)) => accounts,
        _ => return None,
    };
    let mut rows = Vec::with_capacity(accounts.len());
    for account in accounts {
        let key = as_key(obj_get(account, "key"))?;
        rows.push(ViewsAccountRow {
            key,
            cumulative_mbits: as_uint(obj_get(account, "cumulative_mbits"))?,
            demanded_mbits: as_uint(obj_get(account, "demanded_mbits"))?,
            subject_entropy_mbits: as_uint(obj_get(account, "subject_entropy_mbits"))?,
        });
    }
    Some(rows)
}

fn views_in_domain(key: &[String], domains: &Json) -> bool {
    let prefixes = match domains {
        Json::Null => return true,
        Json::Array(prefixes) => prefixes,
        _ => unreachable!("admissibility checked"),
    };
    prefixes.iter().any(|prefix| {
        let parts = as_key(Some(prefix)).expect("admissibility checked");
        key.len() >= parts.len() && key[..parts.len()] == parts[..]
    })
}

/// Exactly §1.5's arithmetic, generalized: cap the fraction at 1, integer
/// cross-multiplication, first satisfied boundary wins.
fn views_classify(cumulative: i64, entropy: i64, policy: &Json) -> String {
    let c = cumulative.min(entropy);
    let classes = match obj_get(policy, "classes") {
        Some(Json::Array(classes)) => classes,
        _ => unreachable!("admissibility checked"),
    };
    for class in classes {
        let max_permille = as_uint(obj_get(class, "max_permille")).expect("admissibility checked");
        if c * 1000 <= max_permille * entropy {
            return as_string(obj_get(class, "label"))
                .expect("admissibility checked")
                .to_string();
        }
    }
    as_string(obj_get(policy, "terminal_label"))
        .expect("admissibility checked")
        .to_string()
}

/// The charge-views/1 computation (VIEWS-SPEC §V.3/§V.4): the report, or
/// the refusal {"spec": ..., "refused": [...]} — never a partial.
pub fn views_report(fold: &Json, policy: &Json) -> Json {
    let mut refused: BTreeSet<String> = BTreeSet::new();
    if !views_policy_admissible(policy) {
        refused.insert(format!(
            "W1 sha256:{}",
            sha256_hex(canonical_json(policy).as_bytes())
        ));
    }
    let rows = views_fold_accounts(fold);
    if rows.is_none() {
        refused.insert(format!(
            "W2 sha256:{}",
            sha256_hex(canonical_json(fold).as_bytes())
        ));
    }
    if !refused.is_empty() {
        let mut out = BTreeMap::new();
        out.insert("spec".to_string(), Json::String(VIEWS_SPEC.to_string()));
        out.insert(
            "refused".to_string(),
            Json::Array(refused.into_iter().map(Json::String).collect()),
        );
        return Json::Object(out);
    }
    let mut rows = rows.expect("checked above");
    rows.sort_by_key(|row| canonical_json(&json_string_array(&row.key)));
    let domains = obj_get(policy, "domains").expect("admissibility checked");
    let incident_permille =
        as_uint(obj_get(policy, "incident_permille")).expect("admissibility checked");
    let accounts: Vec<Json> = rows
        .iter()
        .map(|row| {
            let (class, incident) = if views_in_domain(&row.key, domains) {
                (
                    Json::String(views_classify(
                        row.cumulative_mbits,
                        row.subject_entropy_mbits,
                        policy,
                    )),
                    Json::Bool(
                        row.demanded_mbits * 1000 >= incident_permille * row.subject_entropy_mbits,
                    ),
                )
            } else {
                (Json::String("void".to_string()), Json::Null)
            };
            let mut out = BTreeMap::new();
            out.insert("key".to_string(), json_string_array(&row.key));
            out.insert("class".to_string(), class);
            out.insert("incident".to_string(), incident);
            out.insert(
                "cumulative_mbits".to_string(),
                Json::Int(row.cumulative_mbits),
            );
            out.insert("demanded_mbits".to_string(), Json::Int(row.demanded_mbits));
            out.insert(
                "subject_entropy_mbits".to_string(),
                Json::Int(row.subject_entropy_mbits),
            );
            Json::Object(out)
        })
        .collect();
    let mut out = BTreeMap::new();
    out.insert("spec".to_string(), Json::String(VIEWS_SPEC.to_string()));
    out.insert(
        "policy_name".to_string(),
        Json::String(
            as_string(obj_get(policy, "name"))
                .expect("admissibility checked")
                .to_string(),
        ),
    );
    out.insert(
        "policy_sha256".to_string(),
        Json::String(sha256_hex(canonical_json(policy).as_bytes())),
    );
    out.insert("accounts".to_string(), Json::Array(accounts));
    Json::Object(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sha256_vectors() {
        assert_eq!(
            sha256_hex(b""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
        assert_eq!(
            sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn canonical_escapes_non_ascii() {
        assert_eq!(
            canonical_json(&Json::String("a\né𐐷".to_string())),
            "\"a\\n\\u00e9\\ud801\\udc37\""
        );
    }
}
