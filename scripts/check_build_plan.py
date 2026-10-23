#!/usr/bin/env python3
"""Check canonical roadmap traceability; this is not BCF admission or runtime proof."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class InvalidPlan(ValueError):
    """A candidate obligation was lost or misrepresented in canonical planning."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise InvalidPlan(code)


def load_inputs(root: Path) -> dict:
    def read(path: str) -> dict:
        return yaml.safe_load((root / path).read_text(encoding="utf-8"))

    construction = root / "spec/clauditor/v1/construction"
    return {
        "model": read("spec/clauditor/v1/model.json"),
        "candidate": read("spec/clauditor/v1/construction/plan.json"),
        "build": read("plans/build-plan.yml"),
        "product": read("plans/product-spec.yml"),
        "orders": {p.stem: json.loads(p.read_text(encoding="utf-8"))
                   for p in sorted((construction / "orders").glob("*.json"))},
        "phases": {f"P{n:02d}": {
            "plan": read(f"plans/phase-{n:02d}-plan.yml"),
            "workitems": read(f"plans/phase-{n:02d}-workitems.yml"),
            "log": read(f"phases/phase-{n:02d}-log.yml"),
        } for n in range(1, 10)},
    }


def validate(data: dict) -> dict:
    candidate = data["candidate"]
    rows = candidate["work_orders"]
    orders = data["orders"]
    require(len(rows) == len(orders) == 45, "packet_population")
    ids = [row["id"] for row in rows]
    require(len(set(ids)) == len(ids) and set(ids) == set(orders), "packet_population")
    phases = data["phases"]
    expected_phases = [f"P{n:02d}" for n in range(1, 10)]
    build_rows = data["build"]["phase_sequence"]
    require([p["phase_id"] for p in build_rows] == expected_phases, "phase_catalog")
    require([p["phase_id"] for p in data["product"]["execution_phases"]] == expected_phases,
            "phase_catalog")
    represented = {}
    for pid, phase in phases.items():
        workitems = phase["workitems"]["workitems"]
        require(len({w["id"] for w in workitems}) == len(workitems), "duplicate_workitem")
        require([(w["id"], w["status"]) for w in workitems] ==
                [(w["id"], w["status"]) for w in phase["log"]["workitems"]],
                "phase_log_drift")
        for workitem in workitems:
            if workitem["id"] in orders:
                require(workitem["id"] not in represented, "duplicate_packet")
                represented[workitem["id"]] = (pid, workitem)
    require(set(represented) == set(ids), "canonical_packet_coverage")
    required = {r["id"] for r in data["model"]["requirements"]}
    covered = set()
    for row in rows:
        oid = row["id"]
        packet = orders[oid]
        pid, item = represented[oid]
        require(pid == row["phase"] == packet["proposed_phase"], "packet_phase_drift")
        require(item["summary"] == row["title"], "outcome_drift")
        acceptance = set(item["acceptance"])
        require(f"packet:{oid}" in acceptance, "packet_traceability")
        for rid in packet["A_identity_outcome"]["requirements"]:
            require(rid in required and f"requirement:{rid}" in acceptance,
                    "requirement_traceability")
            covered.add(rid)
        require(set(packet["G_positive_negative_proof"]["positive"]) <= acceptance,
                "positive_acceptance_lost")
        require({"Reject: " + s for s in packet["G_positive_negative_proof"]["negative"]}
                <= acceptance, "negative_acceptance_lost")
        for dep in row["depends_on"]:
            require(dep in orders, "unknown_predecessor")
            same_phase = orders[dep]["proposed_phase"] == pid
            prefix = "requires-workitem-closure:" if same_phase else "predecessor-output:"
            require(prefix + dep in acceptance, "predecessor_lost")
        scope = "\n".join(s["statement"] for s in phases[pid]["plan"]["scope_lock"])
        require(packet["D_proposed_permitted_cut"]["primary_output"] in scope,
                "output_handoff_lost")
        require(all(root in scope for root in row["write_roots"]), "write_scope_lost")
    require(covered == required, "requirement_coverage")
    done = set()
    for wave in candidate["waves"]:
        current = wave["work_orders"]
        require(not (set(current) & done), "duplicate_wave_packet")
        for oid in current:
            require(set(orders[oid]["scheduling"]["depends_on"]) <= done,
                    "dependency_schedule")
        done.update(current)
    require(done == set(ids), "schedule_coverage")
    gates = {g["id"]: g for g in data["build"]["global_gates"]}
    require(gates.get("G2", {}).get("applies_before") == "P02", "construction_boundary")
    rules = " ".join(data["build"]["global_delivery_rules"])
    require("pause" in rules and "substantial construction" in rules,
            "mandatory_pause_missing")
    require(any(w["id"] == "P01-P0-03" for w in phases["P01"]["workitems"]["workitems"]),
            "promotion_workitem_missing")
    return {"status": "canonical_planning_traceability_valid", "requirements": len(required),
            "packets": len(ids), "phases": len(phases), "runtime_authority": False,
            "release_authority": False}


def self_test(data: dict) -> list[str]:
    def remove_packet(changed: dict) -> None:
        changed["phases"]["P02"]["workitems"]["workitems"].pop()
        changed["phases"]["P02"]["log"]["workitems"].pop()

    cases = [
        ("lost_packet", remove_packet, "canonical_packet_coverage"),
        ("lost_negative", lambda d: d["phases"]["P02"]["workitems"]["workitems"][0]
         ["acceptance"].remove("Reject: Agent guesses cannot resolve missing stakeholder policy"),
         "negative_acceptance_lost"),
        ("lost_predecessor", lambda d: d["phases"]["P02"]["workitems"]["workitems"][3]
         ["acceptance"].remove("requires-workitem-closure:CL-WO-001"), "predecessor_lost"),
        ("construction_before_promotion", lambda d: d["build"]["global_gates"][1]
         .__setitem__("applies_before", "P09"), "construction_boundary"),
        ("invalid_wave", lambda d: d["candidate"]["waves"][0]["work_orders"]
         .append("CL-WO-014"), "dependency_schedule"),
    ]
    killed = []
    for name, mutate, expected in cases:
        changed = copy.deepcopy(data)
        mutate(changed)
        try:
            validate(changed)
        except InvalidPlan as error:
            require(str(error) == expected, f"wrong_negative_oracle:{name}:{error}")
            killed.append(name)
        else:
            raise InvalidPlan(f"negative_control_survived:{name}")
    return killed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = load_inputs(ROOT)
    report = validate(data)
    if args.self_test:
        report["negative_controls"] = self_test(data)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
