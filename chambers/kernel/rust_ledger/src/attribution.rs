use std::collections::{BTreeMap, BTreeSet, VecDeque};

use super::{as_bool, as_key, as_string, as_uint, canonical_json, kind, obj_get, Json, Ledger};

const NMAX: usize = 12;

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct AttributionShare {
    pub(crate) share_bps: i64,
    pub(crate) payout_ucr: i64,
}

#[derive(Debug, Clone)]
struct Game {
    shares: BTreeMap<String, AttributionShare>,
    positive_sources: BTreeSet<String>,
}

#[derive(Debug, Clone)]
struct DeclaredShare {
    source: String,
    share_bps: i64,
    payout_ucr: i64,
}

pub fn attribution_findings(ledger: &Ledger) -> Vec<String> {
    let mut findings = BTreeSet::new();

    for report in ledger
        .events
        .values()
        .filter(|event| kind(&event.value) == Some("attribution_report"))
    {
        let pot_ucr = as_uint(obj_get(&report.value, "pot_ucr"));
        let derived = as_string(obj_get(&report.value, "derived"));
        let coupling = report_coupling(&report.value);
        let method_ok = as_string(obj_get(&report.value, "method")) == Some("shapley_dpi/1");
        let declared = declared_shares(&report.value);

        if let (Some(pot_ucr), Some((shares, _))) = (pot_ucr, declared.as_ref()) {
            let payout_sum = shares
                .iter()
                .map(|share| share.payout_ucr as u128)
                .sum::<u128>();
            let bps_sum = shares
                .iter()
                .map(|share| share.share_bps as u128)
                .sum::<u128>();
            if payout_sum != pot_ucr as u128 || (!shares.is_empty() && bps_sum != 10_000) {
                findings.insert(format!("V2 {}", report.id));
            }
        }

        let malformed = pot_ucr.is_none()
            || derived.is_none()
            || coupling.is_none()
            || !method_ok
            || declared.is_none()
            || declared.as_ref().is_some_and(|(_, duplicate)| *duplicate);
        if malformed {
            findings.insert(format!("V5 {}", report.id));
            continue;
        }

        let pot_ucr = pot_ucr.expect("checked above");
        let derived = derived.expect("checked above");
        let (node, tick) = coupling.expect("checked above");
        let (declared, _) = declared.expect("checked above");
        let Some(game) = compute_game(ledger, derived, node, tick, pot_ucr) else {
            findings.insert(format!("V5 {}", report.id));
            continue;
        };

        let mut declared_sources = BTreeSet::new();
        for share in declared {
            declared_sources.insert(share.source.clone());
            let subject = attribution_subject(derived, &share.source);
            let Some(expected) = game.shares.get(&share.source) else {
                findings.insert(format!("V3 {subject}"));
                continue;
            };
            if share.share_bps != expected.share_bps || share.payout_ucr != expected.payout_ucr {
                findings.insert(format!("V1 {subject}"));
            }
        }

        for source in &game.positive_sources {
            if !declared_sources.contains(source) {
                findings.insert(format!("V4 {}", attribution_subject(derived, source)));
            }
        }
    }

    findings.into_iter().collect()
}

pub fn attribution_codes(ledger: &Ledger) -> Vec<String> {
    attribution_findings(ledger)
}

pub(crate) fn recomputed_shares(
    ledger: &Ledger,
    derived: &str,
    node: &Json,
    tick: &Json,
    pot_ucr: i64,
) -> Option<BTreeMap<String, AttributionShare>> {
    let game = compute_game(ledger, derived, node, tick, pot_ucr)?;
    Some(
        game.shares
            .into_iter()
            .filter(|(source, _)| game.positive_sources.contains(source))
            .collect(),
    )
}

fn report_coupling(value: &Json) -> Option<(&Json, &Json)> {
    let Json::Object(fields) = obj_get(value, "coupling")? else {
        return None;
    };
    Some((fields.get("node")?, fields.get("tick")?))
}

fn declared_shares(value: &Json) -> Option<(Vec<DeclaredShare>, bool)> {
    let Json::Array(rows) = obj_get(value, "shares")? else {
        return None;
    };
    let mut shares = Vec::with_capacity(rows.len());
    let mut sources = BTreeSet::new();
    let mut duplicate = false;
    for row in rows {
        let source = as_string(obj_get(row, "source"))?.to_string();
        let share_bps = as_uint(obj_get(row, "share_bps"))?;
        let payout_ucr = as_uint(obj_get(row, "payout_ucr"))?;
        if !sources.insert(source.clone()) {
            duplicate = true;
        }
        shares.push(DeclaredShare {
            source,
            share_bps,
            payout_ucr,
        });
    }
    Some((shares, duplicate))
}

fn attribution_subject(derived: &str, source: &str) -> String {
    canonical_json(&Json::Array(vec![
        Json::String("att".to_string()),
        Json::String(derived.to_string()),
        Json::String(source.to_string()),
    ]))
}

fn compute_game(
    ledger: &Ledger,
    derived: &str,
    node: &Json,
    tick: &Json,
    pot_ucr: i64,
) -> Option<Game> {
    let emission_capacity = emission_capacity(ledger, derived, node, tick)?;
    let graph = ProvenanceGraph::from_ledger(ledger, derived, emission_capacity);
    let sources: Vec<String> = graph.anchors.keys().cloned().collect();
    if sources.len() > NMAX {
        return None;
    }

    let coalition_count = 1usize << sources.len();
    let mut values = Vec::with_capacity(coalition_count);
    for mask in 0..coalition_count {
        values.push(graph.coalition_value(&sources, mask));
    }

    let factorials = factorials(sources.len());
    let mut numerators = vec![0u128; sources.len()];
    for (index, numerator) in numerators.iter_mut().enumerate() {
        let bit = 1usize << index;
        for mask in 0..coalition_count {
            if mask & bit != 0 {
                continue;
            }
            let size = mask.count_ones() as usize;
            let weight = factorials[size] * factorials[sources.len() - 1 - size];
            let marginal = values[mask | bit].saturating_sub(values[mask]) as u128;
            *numerator += weight * marginal;
        }
    }

    let denominator = numerators.iter().sum::<u128>();
    let bps = allocate(10_000, &sources, &numerators, denominator);
    let payouts = allocate(pot_ucr as u128, &sources, &numerators, denominator);
    let mut shares = BTreeMap::new();
    let mut positive_sources = BTreeSet::new();
    for (index, source) in sources.into_iter().enumerate() {
        if numerators[index] > 0 {
            positive_sources.insert(source.clone());
        }
        shares.insert(
            source,
            AttributionShare {
                share_bps: bps[index] as i64,
                payout_ucr: payouts[index] as i64,
            },
        );
    }
    Some(Game {
        shares,
        positive_sources,
    })
}

fn emission_capacity(ledger: &Ledger, derived: &str, node: &Json, tick: &Json) -> Option<i64> {
    let channel = format!("derived:{derived}");
    ledger
        .events
        .values()
        .filter(|event| kind(&event.value) == Some("charge"))
        .filter(|event| obj_get(&event.value, "node") == Some(node))
        .filter(|event| obj_get(&event.value, "tick") == Some(tick))
        .filter(|event| as_string(obj_get(&event.value, "channel")) == Some(channel.as_str()))
        .filter(|event| as_bool(obj_get(&event.value, "accepted")) == Some(true))
        .filter(|event| as_string(obj_get(&event.value, "reason_class")) == Some("EMITTED"))
        .filter(|event| {
            as_key(obj_get(&event.value, "key"))
                .is_some_and(|key| key.first().map(String::as_str) == Some("exp"))
        })
        .filter_map(|event| as_uint(obj_get(&event.value, "estimate_total_mbits")))
        .max()
}

#[derive(Debug, Clone)]
struct ProvenanceGraph {
    sink: String,
    emission_capacity: i64,
    edges: Vec<(String, String, i64)>,
    anchors: BTreeMap<String, BTreeSet<String>>,
}

impl ProvenanceGraph {
    fn from_ledger(ledger: &Ledger, sink: &str, emission_capacity: i64) -> Self {
        let mut all_edges = Vec::new();
        for event in ledger
            .events
            .values()
            .filter(|event| kind(&event.value) == Some("derivation"))
        {
            let Some(derived) = as_string(obj_get(&event.value, "derived")) else {
                continue;
            };
            let Some(capacity) = as_uint(obj_get(&event.value, "hop_capacity_mbits")) else {
                continue;
            };
            let Some(Json::Array(consumed)) = obj_get(&event.value, "consumed") else {
                continue;
            };
            if consumed.iter().any(|item| !matches!(item, Json::String(_))) {
                continue;
            }
            for item in consumed {
                let Json::String(source) = item else {
                    unreachable!("checked above");
                };
                all_edges.push((source.clone(), derived.to_string(), capacity));
            }
        }

        let mut closure = BTreeSet::from([sink.to_string()]);
        loop {
            let mut changed = false;
            for (source, target, _) in &all_edges {
                if closure.contains(target) && closure.insert(source.clone()) {
                    changed = true;
                }
            }
            if !changed {
                break;
            }
        }

        let edges = all_edges
            .into_iter()
            .filter(|(source, target, _)| closure.contains(source) && closure.contains(target))
            .collect::<Vec<_>>();
        let mut anchors: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
        for event in ledger.events.values() {
            if !closure.contains(&event.id) {
                continue;
            }
            let Some(key) = as_key(obj_get(&event.value, "key")) else {
                continue;
            };
            if key.first().map(String::as_str) != Some("exp") || key.len() < 2 {
                continue;
            }
            anchors
                .entry(key[1].clone())
                .or_default()
                .insert(event.id.clone());
        }

        Self {
            sink: sink.to_string(),
            emission_capacity,
            edges,
            anchors,
        }
    }

    fn coalition_value(&self, sources: &[String], mask: usize) -> i64 {
        if mask == 0 || self.emission_capacity == 0 {
            return 0;
        }
        let mut nodes = BTreeSet::from([self.sink.clone()]);
        for (source, target, _) in &self.edges {
            nodes.insert(source.clone());
            nodes.insert(target.clone());
        }
        let nodes: Vec<String> = nodes.into_iter().collect();
        let indices: BTreeMap<String, usize> = nodes
            .iter()
            .enumerate()
            .map(|(index, node)| (node.clone(), index))
            .collect();
        let super_index = nodes.len();
        let mut capacity = vec![vec![0i64; nodes.len() + 1]; nodes.len() + 1];
        for (source, target, edge_capacity) in &self.edges {
            let from = indices[source];
            let to = indices[target];
            capacity[from][to] =
                capacity[from][to].saturating_add((*edge_capacity).min(self.emission_capacity));
        }
        for (index, source) in sources.iter().enumerate() {
            if mask & (1usize << index) == 0 {
                continue;
            }
            if let Some(anchors) = self.anchors.get(source) {
                for anchor in anchors {
                    let anchor_index = indices[anchor];
                    capacity[super_index][anchor_index] = self.emission_capacity;
                }
            }
        }
        max_flow(
            capacity,
            super_index,
            indices[&self.sink],
            self.emission_capacity,
        )
    }
}

fn max_flow(mut residual: Vec<Vec<i64>>, source: usize, sink: usize, limit: i64) -> i64 {
    if source == sink {
        return limit;
    }
    let mut flow = 0i64;
    while flow < limit {
        let mut parent = vec![None; residual.len()];
        parent[source] = Some(source);
        let mut queue = VecDeque::from([source]);
        while let Some(from) = queue.pop_front() {
            for to in 0..residual.len() {
                if parent[to].is_none() && residual[from][to] > 0 {
                    parent[to] = Some(from);
                    if to == sink {
                        break;
                    }
                    queue.push_back(to);
                }
            }
            if parent[sink].is_some() {
                break;
            }
        }
        if parent[sink].is_none() {
            break;
        }
        let mut increment = limit - flow;
        let mut cursor = sink;
        while cursor != source {
            let previous = parent[cursor].expect("path established");
            increment = increment.min(residual[previous][cursor]);
            cursor = previous;
        }
        cursor = sink;
        while cursor != source {
            let previous = parent[cursor].expect("path established");
            residual[previous][cursor] -= increment;
            residual[cursor][previous] = residual[cursor][previous].saturating_add(increment);
            cursor = previous;
        }
        flow += increment;
    }
    flow
}

fn factorials(n: usize) -> Vec<u128> {
    let mut out = vec![1u128; n + 1];
    for index in 1..=n {
        out[index] = out[index - 1] * index as u128;
    }
    out
}

fn allocate(total: u128, sources: &[String], numerators: &[u128], denominator: u128) -> Vec<u128> {
    if denominator == 0 {
        return vec![0; numerators.len()];
    }
    let mut allocations = Vec::with_capacity(numerators.len());
    let mut remainders = Vec::with_capacity(numerators.len());
    for numerator in numerators {
        let (quotient, remainder) = mul_div_rem(total, *numerator, denominator);
        allocations.push(quotient);
        remainders.push(remainder);
    }
    let shortfall = remainders.iter().sum::<u128>() / denominator;
    let mut order: Vec<usize> = (0..sources.len()).collect();
    order.sort_by(|left, right| {
        remainders[*right]
            .cmp(&remainders[*left])
            .then_with(|| sources[*left].cmp(&sources[*right]))
    });
    for index in order.into_iter().take(shortfall as usize) {
        allocations[index] += 1;
    }
    allocations
}

fn mul_div_rem(multiplier: u128, multiplicand: u128, divisor: u128) -> (u128, u128) {
    let mut quotient = 0u128;
    let mut remainder = 0u128;
    for bit in (0..128).rev() {
        quotient *= 2;
        remainder *= 2;
        if multiplier & (1u128 << bit) != 0 {
            remainder += multiplicand;
        }
        while remainder >= divisor {
            remainder -= divisor;
            quotient += 1;
        }
    }
    (quotient, remainder)
}
