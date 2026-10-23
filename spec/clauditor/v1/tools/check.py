#!/usr/bin/env python3
"""Deterministic candidate-specification validator and derived-view generator.

This is NOT a BCF EvidenceReceipt, runtime test, construction admission or
release gate. A strict source-registry is checked independently of candidate
edge/transition declarations before any derived exclusion is emitted.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = (
    "identity", "schema", "provenance", "applicability", "authorization",
    "lifecycle", "freshness", "failure", "invalidation", "cost",
)
EXCLUSION = "no_dependency_or_event_path"


class InvalidSpec(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}")


def require(ok: bool, code: str, detail: object = "") -> None:
    if not ok:
        raise InvalidSpec(code, str(detail))


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key", key)
        result[key] = value
    return result


def load(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(), "source_missing", path.name)
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def schema_validate(payload: dict, schema: dict, which: str) -> None:
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(payload),
                    key=lambda e: tuple(map(str, e.absolute_path)))
    if errors:
        err = errors[0]
        raise InvalidSpec("schema_rejected", f"{which}/{'/'.join(map(str, err.absolute_path))}: {err.message}")


def indexed(items: list[dict], label: str) -> dict[str, dict]:
    values = {}
    for entry in items:
        key = entry["id"]
        require(key not in values, "duplicate_identity", f"{label}:{key}")
        values[key] = entry
    return values


def validate(model: dict, source: dict) -> dict:
    schema_validate(model, load(ROOT / "schema/model.schema.json"), "model")
    schema_validate(source, load(ROOT / "schema/source-registry.schema.json"), "sources")
    require(model["document"]["runtime_authority"] is False and
            model["document"]["release_authority"] is False,
            "candidate_claims_authority")
    require(model["document"]["active_profile"] == "lite" and
            model["bcf"].get("current_profile") == "lite",
            "profile_scope")
    require(model["document"]["active_profile"] == "lite" and
            model["bcf"]["persistent_controller"] is False,
            "bcf_profile_boundary")
    require(model["appliance"]["storage"]["target_days"] == 365 and
            model["appliance"]["storage"]["approved_fallback_days"] == 90 and
            model["appliance"]["storage"]["minimum_days"] == 31 and
            model["appliance"]["storage"]["automatic_degradation"] is False,
            "retention_floor")

    ids = []
    for kind in ("owners", "invariants", "laws", "primitives", "requirements",
                 "operations", "state_machines"):
        ids.extend(item["id"] for item in model[kind])
    topo = model["topology"]
    for kind in ("nodes", "flow_obligations", "edge_contracts"):
        ids.extend(item["id"] for item in topo[kind])
    require(len(ids) == len(set(ids)), "global_duplicate_identity")

    owners = indexed(model["owners"], "owners")
    invariants = indexed(model["invariants"], "invariants")
    reqs = indexed(model["requirements"], "requirements")
    ops = indexed(model["operations"], "operations")
    nodes = indexed(topo["nodes"], "nodes")
    srcids = {entry["id"] for entry in source["sources"]}
    require(len(srcids) == len(source["sources"]), "duplicate_source_id")
    for inv in invariants.values():
        require(inv["owner"] in owners, "missing_invariant_owner", inv["id"])
    for law in model["laws"]:
        require(law["owner"] in owners and law["invariants"] and
                set(law["invariants"]) <= set(invariants),
                "law_ownership_or_invariant", law["id"])
    for item in model["primitives"]:
        require(item["owner"] in owners and item["fields"], "primitive_owner", item["id"])
    for req in reqs.values():
        require(req["owner"] in owners and req["invariant"] in invariants and
                set(req["sources"]) <= srcids and
                req["verification"] == "required_not_executed",
                "requirement_source_or_authority", req["id"])
    for operation in ops.values():
        require(operation["owner"] in owners, "operation_owner", operation["id"])
        require(operation["side"] == "command" or not operation["effects"],
                "query_mutates", operation["id"])

    machines = indexed(model["state_machines"], "machines")
    source_trans = {x["machine"]: x for x in source["independent_transition_population"]}
    require(len(source_trans) == len(source["independent_transition_population"]) and
            set(source_trans) == set(machines),
            "independent_transition_population")
    state_matrix = []
    for machine in machines.values():
        mid = machine["id"]
        states, events = machine["states"], machine["events"]
        require(len(states) == len(set(states)) and len(events) == len(set(events)),
                "state_population_duplicates", mid)
        require(machine["owner"] in owners and machine["initial"] in states and
                set(machine["terminal"]) <= set(states),
                "invalid_state_machine", mid)
        require(machine["exclusion"]["kind"] == "typed" and
                machine["exclusion"]["bcf_reason"] == EXCLUSION and
                machine["exclusion"]["law"] == "cl.law.state.v1",
                "untyped_state_exclusion", mid)
        actual_ids = [t["id"] for t in machine["transitions"]]
        expected_ids = source_trans[mid]["required_transition_ids"]
        require(len(actual_ids) == len(set(actual_ids)) and
                set(actual_ids) == set(expected_ids),
                "transition_contract_closure", mid)
        slots: dict[tuple[str, str], dict] = {}
        for t in machine["transitions"]:
            key = (t["from"], t["event"])
            require(key not in slots, "ambiguous_state_event", f"{mid}:{key}")
            require(t["from"] in states and t["to"] in states and t["event"] in events
                    and t["from"] not in machine["terminal"],
                    "illegal_state_transition", t["id"])
            require(t["operation"] in ops, "unknown_transition_operation", t["id"])
            require(ops[t["operation"]]["owner"] == machine["owner"] or
                    (mid == "cl.machine.ingest.v1" and
                     t["operation"] in ("cl.op.preserve.v1","cl.op.index.v1")),
                    "unauthorized_transition_owner", t["id"])
            slots[key] = t
        seen = {machine["initial"]}
        while True:
            extended = seen | {t["to"] for t in machine["transitions"]
                               if t["from"] in seen}
            if extended == seen:
                break
            seen = extended
        require(seen == set(states), "unreachable_declared_state",
                f"{mid}:{sorted(set(states)-seen)}")
        for state in sorted(states):
            for event in sorted(events):
                t = slots.get((state, event))
                state_matrix.append({
                    "machine": mid, "state": state, "event": event,
                    "outcome": "contract" if t else "typed_exclusion",
                    "transition_id": t["id"] if t else "",
                    "reason": "" if t else EXCLUSION,
                })

    producers, consumers = topo["producers"], topo["consumers"]
    require(len(producers) == len(set(producers)) and
            len(consumers) == len(set(consumers)) and
            set(producers) == set(nodes) == set(consumers),
            "node_population_closure")
    require(all(x["owner"] in owners for x in nodes.values()), "node_owner")
    flow = indexed(topo["flow_obligations"], "required_flows")
    edges = indexed(topo["edge_contracts"], "edges")
    profiles = topo["edge_profiles"]
    require(topo["exclusion"]["bcf_reason"] == EXCLUSION and
            topo["exclusion"]["law"] == "cl.law.edge.v1",
            "untyped_edge_exclusion")
    matched = {}
    for edge in edges.values():
        key = edge["flow"]
        require(key not in matched, "duplicate_edge_contract", key)
        matched[key] = edge
    require(set(matched) == set(flow), "missing_edge_contract",
            sorted(set(flow)-set(matched)))
    for expected in flow.values():
        eid = expected["id"]
        edge = matched[eid]
        require(expected["requires"] in reqs and
                expected["producer"] in producers and expected["consumer"] in consumers,
                "unbound_flow", eid)
        for k in ("producer", "consumer", "artifact", "profile"):
            require(edge[k] == expected[k], "edge_binding_mismatch", eid + ":" + k)
        profile = profiles.get(edge["profile"])
        require(profile is not None and
                all(isinstance(profile.get(k), str) and len(profile[k]) >= 10
                    for k in DIMENSIONS),
                "edge_dimensions_incomplete", eid)

    required_pairs = {(f["producer"], f["consumer"]) for f in flow.values()}
    source_edges = (source["independent_required_source_edges"] +
                    source["independent_required_safety_edges"])
    for obligation in source_edges:
        pair = (obligation["producer"], obligation["consumer"])
        require(pair in required_pairs and obligation["source_ref"] in srcids,
                "independent_required_route_missing", pair)
    pairs = {}
    for expected in flow.values():
        key = (expected["producer"], expected["consumer"])
        pairs.setdefault(key, []).append(expected["id"])
    edge_matrix = []
    for producer in sorted(producers):
        for consumer in sorted(consumers):
            routes = sorted(pairs.get((producer, consumer), []))
            edge_matrix.append({
                "producer": producer, "consumer": consumer,
                "outcome": "contract" if routes else "typed_exclusion",
                "route_ids": routes, "reason": "" if routes else EXCLUSION,
            })
    require(sum(len(x["route_ids"]) for x in edge_matrix) == len(flow),
            "matrix_edge_reconciliation")
    return {
        "counts": {
            "sources": len(srcids), "requirements": len(reqs),
            "invariants": len(invariants), "owners": len(owners),
            "operations": len(ops), "machines": len(machines),
            "state_events": len(state_matrix),
            "state_transitions": sum(x["outcome"] == "contract"
                                     for x in state_matrix),
            "state_exclusions": sum(x["outcome"] == "typed_exclusion"
                                    for x in state_matrix),
            "producer_consumer_pairs": len(edge_matrix),
            "edge_contracts": len(flow),
            "edge_exclusions": sum(x["outcome"] == "typed_exclusion"
                                   for x in edge_matrix),
        },
        "edge_matrix": edge_matrix, "state_matrix": state_matrix,
        "runtime_authority": False, "release_authority": False,
    }


def mutation_controls(model: dict, source: dict) -> dict:
    cases = []
    def negative(name: str, mutate, required_codes: set[str]) -> None:
        m, s = copy.deepcopy(model), copy.deepcopy(source)
        mutate(m, s)
        try:
            validate(m, s)
        except InvalidSpec as exc:
            require(exc.code in required_codes, "wrong_negative_oracle", f"{name}:{exc.code}")
            cases.append({"id": name, "detected": True, "failure_code": exc.code})
        else:
            raise InvalidSpec("semantic_mutation_survived", name)

    negative("missing_exact_edge",
             lambda m,s: m["topology"]["edge_contracts"].pop(0),
             {"missing_edge_contract"})
    negative("deleting_route_and_contract_is_not_an_exclusion",
             lambda m,s: (m["topology"]["edge_contracts"].pop(0),
                          m["topology"]["flow_obligations"].pop(0)),
             {"independent_required_route_missing"})
    negative("false_exclusion_kind",
             lambda m,s: m["topology"]["exclusion"].__setitem__(
                 "bcf_reason", "because_it_is_missing"), {"untyped_edge_exclusion"})
    negative("missing_transition",
             lambda m,s: m["state_machines"][0]["transitions"].pop(0),
             {"transition_contract_closure"})
    negative("missing_cost_dimension",
             lambda m,s: m["topology"]["edge_profiles"]["source"].pop("cost"),
             {"schema_rejected"})
    negative("removed_excluded_only_producer",
             lambda m,s: m["topology"]["producers"].pop(0),
             {"node_population_closure"})
    negative("query_acquires_mutating_effect",
             lambda m,s: next(o for o in m["operations"]
                 if o["side"] == "query")["effects"].append("write"),
             {"query_mutates"})
    return {"causal_mutations_killed": len(cases), "cases": cases,
            "runtime_authority": False}


def as_csv(rows: list[dict], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(row[k], sort_keys=True)
                         if isinstance(row[k], list) else row[k] for k in fields})
    return stream.getvalue().encode("utf-8")


def render(model: dict, source: dict, result: dict) -> dict[str, bytes]:
    lines = [
        "# Clauditor — generated candidate product specification",
        "",
        "**Candidate only.** Not a BCF EvidenceReceipt or construction/release admission.",
        "",
        "## Scope",
        "",
    ]
    lines += ["- " + item for item in model["scope"]["included"]]
    lines += ["", "## Explicit exclusions", ""]
    lines += ["- " + item for item in model["scope"]["excluded"]]
    lines += ["", "## Invariants and owners", ""]
    lines += ["- " + i["id"] + " — " + i["property"] +
              " (owner: " + i["owner"] + ")" for i in model["invariants"]]
    lines += ["", "## Requirements", ""]
    for r in model["requirements"]:
        lines += ["### " + r["id"], r["statement"], "",
                  "- Sources: " + ", ".join(r["sources"]),
                  "- Canonical owner: " + r["owner"],
                  "- Invariant: " + r["invariant"],
                  "- Positive proof required: " + r["acceptance"]["positive"],
                  "- Negative proof required: " + r["acceptance"]["negative"], ""]
    lines += ["## Mechanical closure (candidate model)", ""]
    lines += [f"- {k}: {v}" for k,v in result["counts"].items()]
    lines += ["", "## Known external qualification gaps", ""]
    lines += ["- " + x["id"] + ": " + x["issue"]
              for x in model["open_questions"]]
    lines += ["", "## Admission", "",
              "Complete local model checks do not establish correct stakeholder intent, "
              "actual Anthropic source coverage, production runtime behavior, "
              "or BCF Standard-v3 admission.", ""]
    edges = result["edge_matrix"]
    states = result["state_matrix"]
    dot = ['digraph clauditor {', '  rankdir=LR;']
    for e in edges:
        if e["outcome"] == "contract":
            dot.append('  ' + json.dumps(e["producer"]) + " -> " +
                       json.dumps(e["consumer"]) + " [label=" +
                       json.dumps(str(len(e["route_ids"])) + " flows") + "];")
    dot.append("}")
    contents = {
        "Clauditor_Specification.md": ("\n".join(lines)).encode("utf-8"),
        "producer-consumer.csv": as_csv(edges,
              ["producer","consumer","outcome","route_ids","reason"]),
        "state-event.csv": as_csv(states,
              ["machine","state","event","outcome","transition_id","reason"]),
        "producer-consumer.dot": ("\n".join(dot) + "\n").encode("utf-8"),
    }
    inputs = {
        name: sha((ROOT / name).read_bytes())
        for name in ("model.json", "source-registry.json",
                     "schema/model.schema.json",
                     "schema/source-registry.schema.json")
    }
    contents["manifest.json"] = (
        json.dumps({
            "id": "cl.derived.manifest.v1", "source_inputs": inputs,
            "output_digests": {name: sha(data) for name, data in sorted(contents.items())},
            "runtime_authority": False, "release_authority": False,
        }, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    return contents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="Cause-specific negative mutation probes of candidate model")
    parser.add_argument("--emit-dir", type=Path,
                        help="Optional derived-only output outside canonical spec")
    args = parser.parse_args()
    model, source = load(ROOT / "model.json"), load(ROOT / "source-registry.json")
    result = validate(model, source)
    output = {"status":"candidate_structure_valid", "counts": result["counts"],
              "runtime_authority": False, "release_authority": False}
    if args.self_test:
        output["mutations"] = mutation_controls(model, source)
    if args.emit_dir:
        outdir = args.emit_dir.resolve()
        require(not outdir.is_relative_to(ROOT), "output_inside_canonical_spec",
                "Use a temporary or ignored generated directory")
        outdir.mkdir(parents=True, exist_ok=True)
        artifacts = render(model, source, result)
        for path, data in sorted(artifacts.items()):
            (outdir / path).write_bytes(data)
        output["derived"] = {"directory": str(outdir),
                             "files": len(artifacts)}
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
