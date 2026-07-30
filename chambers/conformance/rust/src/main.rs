//! Trace runner for `egress-accountant/1`.
//!
//!   cargo run -- --check           # replay every trace, assert bit-for-bit, exit nonzero on any divergence
//!   cargo run -- --emit <dir>      # write <name>.actual.json (JSON array of Decisions) per trace
//!
//! Traces live in ../traces relative to this crate.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::exit;

use egress_accountant::{diff_decision, load_trace, replay};

fn traces_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("..").join("traces")
}

fn trace_files() -> Vec<PathBuf> {
    let mut v: Vec<PathBuf> = fs::read_dir(traces_dir())
        .expect("traces dir")
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.extension().map(|x| x == "json").unwrap_or(false))
        .filter(|p| p.file_name().map(|n| n != "MANIFEST.json").unwrap_or(false))
        .collect();
    v.sort();
    v
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("--check");

    match mode {
        "--check" => {
            let mut fails = 0;
            let mut n = 0;
            for path in trace_files() {
                let trace = load_trace(&fs::read_to_string(&path).unwrap());
                let actual = replay(&trace);
                if actual.len() != trace.expected.len() {
                    println!("FAIL {}: {} decisions != {} expected", trace.name, actual.len(), trace.expected.len());
                    fails += 1;
                    continue;
                }
                for (i, (a, e)) in actual.iter().zip(trace.expected.iter()).enumerate() {
                    if let Some(field) = diff_decision(a, e) {
                        println!("FAIL {}[{}].{}: rust produced {}", trace.name, i, field, a.to_json());
                        fails += 1;
                    }
                }
                n += 1;
            }
            if fails > 0 {
                println!("CONFORMANCE FAIL: {fails} divergences across {n} traces");
                exit(1);
            }
            println!("CONFORMANCE OK (rust): {n} traces agree bit-for-bit");
        }
        "--emit" => {
            let out = PathBuf::from(args.get(2).expect("usage: --emit <dir>"));
            fs::create_dir_all(&out).unwrap();
            let mut n = 0;
            for path in trace_files() {
                let trace = load_trace(&fs::read_to_string(&path).unwrap());
                let decisions = replay(&trace);
                let body: Vec<String> = decisions.iter().map(|d| d.to_json()).collect();
                let json = format!("[{}]", body.join(","));
                fs::write(out.join(format!("{}.actual.json", trace.name)), json + "\n").unwrap();
                n += 1;
            }
            println!("emitted {n} actual streams to {}", out.display());
        }
        other => {
            eprintln!("unknown mode {other:?}; use --check or --emit <dir>");
            exit(2);
        }
    }
}
