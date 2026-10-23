#!/usr/bin/env python3
"""Deterministic source-pinned A-J plan validation, not BCF admission."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
from collections import Counter
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT.parent
REPO = ROOT.parents[3]

class PlanningError(ValueError):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(code + ": " + str(detail))

def require(ok, code, detail=""):
    if not ok:
        raise PlanningError(code, detail)

def no_duplicates(pairs):
    out = {}
    for key,value in pairs:
        require(key not in out, "duplicate_json_key", key)
        out[key] = value
    return out

def load(path):
    require(path.is_file() and not path.is_symlink(), "missing_source", path)
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)

def sha_git(path):
    b=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def check_schema(value, filename):
    schema=load(ROOT/"schema"/filename)
    Draft202012Validator.check_schema(schema)
    errors=list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        e=errors[0]
        raise PlanningError("schema_rejected", filename+":"+
                            "/".join(map(str,e.absolute_path))+":"+e.message)

def overlap(a,b):
    a,b=a.rstrip("/"),b.rstrip("/")
    return a==b or a.startswith(b+"/") or b.startswith(a+"/")

def read_orders(index):
    out={}
    for entry in index["orders"]:
        ident=entry["id"]
        require(entry["path"]=="orders/"+ident+".json" and ident not in out,
                "order_index_identity",ident)
        out[ident]=load(ROOT/"orders"/(ident+".json"))
    files={p.name for p in (ROOT/"orders").glob("*.json")}
    require(files=={ident+".json" for ident in out},"order_inventory_closure")
    return out

def validate(plan, orders, index, model, src):
    check_schema(plan,"plan.schema.json")
    for oid,packet in orders.items():
        check_schema(packet,"order.schema.json")
        require(oid==packet["id"],"order_identity",oid)
    header=plan["document"]
    require(header["source_model_blob"]==sha_git(SPEC/"model.json") and
            header["source_registry_blob"]==sha_git(SPEC/"source-registry.json"),
            "source_blob_drift")
    require(header["status"]=="draft_not_admitted" and
            header["active_bcf_profile"]=="lite" and
            header["bcf_release"]=="v2.3.6" and
            not header["runtime_authority"] and
            not header["release_authority"] and
            index["document"]["status"]=="candidate_only" and
            index["document"]["baseline"]==header["source_commit"],
            "candidate_authority")
    reqs={x["id"]:(i,x) for i,x in enumerate(model["requirements"])}
    require(len(reqs)==len(model["requirements"]),"duplicate_source_requirement")
    owners={x["id"] for x in model["owners"]}
    invariants={x["id"] for x in model["invariants"]}
    flows={x["id"] for x in model["topology"]["flow_obligations"]}
    refs={x["id"] for x in src["sources"]}
    stubs=plan["work_orders"]
    ids=[x["id"] for x in stubs]
    require(len(ids)==len(set(ids)) and set(ids)==set(orders)==
            {x["id"] for x in index["orders"]},
            "work_order_population_closure")
    by_id={w["id"]:w for w in stubs}
    coverage={rid:[] for rid in reqs}
    for oid,w in by_id.items():
        p=orders[oid]
        A=p["A_identity_outcome"]; B=p["B_authoritative_context"]
        C=p["C_preconditions_readiness"]; D=p["D_proposed_permitted_cut"]
        E=p["E_behavioral_contract"]; G=p["G_positive_negative_proof"]
        J=p["J_completion_handoff"]; sched=p["scheduling"]
        require(p["status"]=="not_admitted" and not w["admitted"] and
                G["result"]=="not_run" and
                J["primary_output"]["status"]=="future_not_built",
                "candidate_authority",oid)
        require(A["id"]==oid and
                A["canonical_domain_owner"]==w["owner"] and w["owner"] in owners and
                A["required_results"]==w["title"] and
                set(A["invariants"])<=invariants and
                set(A["product_edges"])<=flows,
                "owner_or_trace_invalid",oid)
        require(A["requirements"]==w["requirements"] and
                len(set(w["requirements"]))==len(w["requirements"]) and
                p["complexity"]==w["complexity"] and
                p["proposed_phase"]==w["phase"],
                "summary_packet_drift",oid)
        require(w["depends_on"]==sched["depends_on"]==C["dependency_ids"] and
                w["write_roots"]==sched["exclusive_write_roots"]==D["write_roots"] and
                w["locks"]==sched["exclusive_resource_locks"],
                "dependency_or_writer_drift",oid)
        path=D["primary_output"]
        require(not path.startswith("tests/") or path.startswith("tests/fixtures/"),
                "evidence_location", oid)
        require(path==w["primary_output"]==J["primary_output"]["path"] and
                J["primary_output"]["id"]==oid+":primary" and
                E["outputs"]==[oid+":primary"] and
                any(path==r or path.startswith(r) for r in D["write_roots"]),
                "write_scope_escape",oid)
        sr=B["exact_source"]
        require(sr["repo"]=="mjgolaszewski/clauditor" and
                sr["baseline_git_commit"]==header["source_commit"] and
                sr["model_git_blob"]==header["source_model_blob"] and
                sr["registry_git_blob"]==header["source_registry_blob"],
                "packet_source_drift",oid)
        given={r["id"]:r for r in B["requirements"]}
        require(len(given)==len(B["requirements"]) and
                set(given)==set(w["requirements"]),
                "packet_source_coverage",oid)
        for rid,v in given.items():
            require(rid in reqs,"unresolved_requirement",rid)
            i,orig=reqs[rid]
            require(v["source_pointer"]==
                    "spec/clauditor/v1/model.json#/requirements/"+str(i) and
                    v["source_refs"]==orig["sources"] and
                    set(v["source_refs"])<=refs and
                    v["positive"]==orig["acceptance"]["positive"] and
                    v["negative"]==orig["acceptance"]["negative"],
                    "exact_requirement_origin",rid)
            coverage[rid].append(oid)
        prev=B["predecessor_outputs"]
        require(prev==C["consumed_predecessor_outputs"] and
                [x["order_id"] for x in prev]==w["depends_on"],
                "dependency_output_closure",oid)
        for x in prev:
            parent=by_id.get(x["order_id"])
            require(parent is not None and
                    x["required_artifact_id"]==x["order_id"]+":primary" and
                    x["artifact_path"]==parent["primary_output"] and
                    "not yet assigned" in x["qualification"],
                    "dependency_output_closure",oid)
        require(p["F_implementation_approach"]["ordered_steps"] and
                G["positive"] and G["negative"] and
                p["I_discretion_stop"]["stop"] and
                p["H_validation_evidence"]["cost_order"],
                "incomplete_AJ",oid)
    require(all(coverage.values()),"requirement_coverage",
            [k for k,v in coverage.items() if not v])
    require(plan["source_to_orders"]==coverage,
            "requirement_coverage_matrix")
    for oid,p in orders.items():
        successors=[w["id"] for w in stubs if oid in w["depends_on"]]
        require(p["J_completion_handoff"]["downstream_dependents"]==successors,
                "downstream_closure",oid)
    require(ids==["CL-WO-"+str(i+1).zfill(3) for i in range(len(ids))],
            "order_sort")
    done=set(); waves=[]
    while len(done)<len(stubs):
        ready=[w for w in stubs if w["id"] not in done and
               set(w["depends_on"])<=done]
        require(ready,"dependency_cycle")
        occupied=[];locks=set();selected=[]
        for w in ready:
            if any(overlap(r,x) for r in w["write_roots"] for x in occupied):
                continue
            if set(w["locks"]) & locks:
                continue
            selected.append(w["id"])
            occupied.extend(w["write_roots"])
            locks.update(w["locks"])
        require(selected,"resource_schedule_deadlock")
        waves.append(selected);done.update(selected)
    require(waves==[x["work_orders"] for x in plan["waves"]] and
            [x["wave"] for x in plan["waves"]]==list(range(1,len(waves)+1)),
            "wave_dependency_or_resource_conflict")
    stats=plan["statistics"]
    c=Counter(x["complexity"] for x in orders.values())
    require(stats["requirements"]==len(reqs) and
            stats["orders"]==len(stubs) and
            stats["waves"]==len(waves) and
            stats["parallel_waves"]==sum(len(w)>1 for w in waves) and
            stats["complexity"]=={x:c.get(x,0)
                                  for x in ("low","medium","high")},
            "statistics_drift")
    return {"status":"candidate_plan_structure_valid",
            "requirements":len(reqs),"orders":len(orders),"waves":len(waves),
            "parallel_waves":sum(len(w)>1 for w in waves),
            "source_git_blobs_match":True,
            "runtime_authority":False,"release_authority":False}

def mutations(plan, orders, index, model, src):
    passed=[]
    def denied(label,fn,cause):
        p,o,i=copy.deepcopy(plan),copy.deepcopy(orders),copy.deepcopy(index)
        fn(p,o,i)
        try: validate(p,o,i,model,src)
        except PlanningError as e:
            require(e.code==cause,"wrong_mutation_oracle",label+":"+e.code)
            passed.append(label)
        else: raise PlanningError("semantic_mutation_survived",label)
    denied("packet_removed",lambda p,o,i:o.pop("CL-WO-020"),
           "work_order_population_closure")
    denied("coverage_removed",lambda p,o,i:p["source_to_orders"].pop("cl.req.001.v1"),
           "requirement_coverage_matrix")
    denied("predecessor_absent",lambda p,o,i:o["CL-WO-019"]
           ["B_authoritative_context"]["predecessor_outputs"].pop(),
           "dependency_output_closure")
    denied("source_forged",lambda p,o,i:p["document"]
           .__setitem__("source_model_blob","0"*40),"source_blob_drift")
    denied("self_admission",lambda p,o,i:o["CL-WO-027"]
           .__setitem__("status","admitted"),"schema_rejected")
    denied("writer_escapes",lambda p,o,i:o["CL-WO-026"]
           ["D_proposed_permitted_cut"].__setitem__("primary_output",
                                                     "secrets/credential"),
           "write_scope_escape")
    denied("wave_tamper",lambda p,o,i:p["waves"][10]
           ["work_orders"].append("CL-WO-015"),
           "wave_dependency_or_resource_conflict")
    denied("evidence_in_test_tree",lambda p,o,i:o["CL-WO-037"]
           ["D_proposed_permitted_cut"].__setitem__(
               "primary_output", "tests/conformance/source/evidence.json"),
           "evidence_location")
    return {"causal_negative_controls":len(passed),
            "detected":passed,"runtime_authority":False}

def render(plan, orders, report, requested=None):
    lines=["# Clauditor generated construction plan","",
           "**Review-only derivative; no BCF construction admission.**","",
           str(report["orders"])+" orders, "+
           str(report["requirements"])+" requirements, "+
           str(report["waves"])+" dependency waves.","",
           "## Dependency waves",""]
    for wave in plan["waves"]:
        lines.append("Wave "+str(wave["wave"])+": "+
                     ", ".join(wave["work_orders"]))
    lines+=["","## Packets",""]
    for row in plan["work_orders"]:
        lines+=["### "+row["id"]+" "+row["title"],
                "Phase "+row["phase"]+" / "+row["complexity"]+
                " / owner "+row["owner"],
                "Predecessors: "+(", ".join(row["depends_on"]) or "none"),
                "Requirements: "+", ".join(row["requirements"]),"Output: "+
                row["primary_output"],""]
    if requested:
        lines+=["## Full bounded packet "+requested,""]
        for key,val in orders[requested].items():
            if len(key)>2 and key[0] in "ABCDEFGHIJ" and key[1]=="_":
                lines+=["### "+key,"~~~json",
                        json.dumps(val,indent=2,ensure_ascii=False),"~~~",""]
    lines+=["## Open questions",""]
    lines+=["- "+str(q["id"])+": "+q["issue"]
            for q in plan["unresolved"]]
    lines+=["","A generated view does not establish implementation or release authority.",""]
    return "\n".join(lines).encode()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--render-order")
    parser.add_argument("--emit-dir",type=Path)
    args=parser.parse_args()
    plan,index=load(ROOT/"plan.json"),load(ROOT/"index.json")
    orders=read_orders(index)
    model,src=load(SPEC/"model.json"),load(SPEC/"source-registry.json")
    report=validate(plan,orders,index,model,src)
    if args.self_test:
        report["mutations"]=mutations(plan,orders,index,model,src)
    if args.render_order:
        require(args.render_order in orders,"unknown_order",args.render_order)
    if args.emit_dir:
        dest=args.emit_dir.resolve()
        require(not dest.is_relative_to(REPO.resolve()),
                "generated_inside_repository",dest)
        dest.mkdir(parents=True,exist_ok=True)
        name=(args.render_order+"-Packet.md" if args.render_order
              else "Construction-Plan.md")
        view=render(plan,orders,report,args.render_order)
        (dest/name).write_bytes(view)
        (dest/"manifest.json").write_text(json.dumps({
            "id":"cl.construction.derived_manifest.v1",
            "plan_sha256":hashlib.sha256((ROOT/"plan.json").read_bytes()).hexdigest(),
            "view_sha256":hashlib.sha256(view).hexdigest(),
            "runtime_authority":False},indent=2)+"\n")
        report["derived"]=str(dest/name)
    print(json.dumps(report,indent=2,sort_keys=True))

PUBLIC_OPERATIONS = {'validate-construction': main}

if __name__=="__main__":
    main()
