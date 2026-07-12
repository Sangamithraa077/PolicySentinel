"""FastAPI routes for traversing Neo4j knowledge graph and executing policy impact analysis."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
import uuid
import logging

from backend.api.dependencies.database import get_db
from backend.models.policy import Policy
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.regulatory_mapping import RegulatoryMapping
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation
from backend.schemas.graph import GraphResponse, ImpactAnalysisResponse
from backend.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter()


def get_neo4j_client(request: Request) -> Neo4jClient | None:
    """Retrieves current Neo4jClient instance stored in app lifecycle state."""
    return getattr(request.app.state, "neo4j_client", None)


@router.get(
    "/policy/{policy_id}",
    response_model=GraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve policy graph slice"
)
def get_policy_graph(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """Returns nodes and edges mapping a policy, its clauses, obligations, regulations, and findings."""
    nodes = []
    edges = []

    # 1. Attempt to fetch from Neo4j
    if neo4j and neo4j.verify_connectivity():
        try:
            with neo4j.get_session() as session:
                result = session.run(
                    """
                    MATCH (p:Policy {id: $policy_id})
                    OPTIONAL MATCH (p)-[r1:HAS_CLAUSE]->(c:Clause)
                    OPTIONAL MATCH (c)-[r2:HAS_OBLIGATION]->(o:Obligation)
                    OPTIONAL MATCH (o)-[r3:MAPS_TO]->(reg:Regulation)
                    OPTIONAL MATCH (o)-[r4:HAS_FINDING]->(f:Finding)
                    RETURN p, r1, c, r2, o, r3, reg, r4, f
                    """,
                    policy_id=str(policy_id)
                )

                visited = set()
                for record in result:
                    for key in ["p", "c", "o", "reg", "f"]:
                        node = record.get(key)
                        if node and node.element_id not in visited:
                            visited.add(node.element_id)
                            node_type = list(node.labels)[0] if node.labels else "Unknown"
                            nodes.append({
                                "id": node.get("id") or node.get("framework_name") + "_" + node.get("clause_reference", ""),
                                "label": node.get("title") or node.get("clause_number") or node.get("subject") or node.get("clause_reference") or "Node",
                                "type": node_type,
                                "properties": dict(node)
                            })
                    for key in ["r1", "r2", "r3", "r4"]:
                        rel = record.get(key)
                        if rel:
                            src_node = rel.start_node
                            tgt_node = rel.end_node
                            edges.append({
                                "source": src_node.get("id") or src_node.get("framework_name") + "_" + src_node.get("clause_reference", ""),
                                "target": tgt_node.get("id") or tgt_node.get("framework_name") + "_" + tgt_node.get("clause_reference", ""),
                                "type": rel.type,
                                "properties": dict(rel)
                            })
            if nodes:
                return {"nodes": nodes, "edges": edges}
        except Exception as exc:
            logger.error("Neo4j policy graph query failed: %s. Swapping to Postgres fallback.", exc)

    # 2. SQL Fallback
    logger.info("Running SQL query fallback to compute policy graph visualization.")
    policy = db.get(Policy, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found."
        )

    nodes.append({
        "id": str(policy.id),
        "label": policy.title,
        "type": "Policy",
        "properties": {"title": policy.title, "status": policy.status}
    })

    clauses = db.scalars(select(Clause).where(Clause.policy_id == policy_id, Clause.deleted_at.is_(None))).all()
    for cl in clauses:
        nodes.append({
            "id": str(cl.id),
            "label": cl.clause_number or "Clause",
            "type": "Clause",
            "properties": {"clause_number": cl.clause_number, "text": cl.text, "order_index": cl.order_index}
        })
        edges.append({
            "source": str(policy.id),
            "target": str(cl.id),
            "type": "HAS_CLAUSE",
            "properties": {}
        })

        obligations = db.scalars(select(Obligation).where(Obligation.clause_id == cl.id, Obligation.deleted_at.is_(None))).all()
        for ob in obligations:
            nodes.append({
                "id": str(ob.id),
                "label": ob.subject or "Obligation",
                "type": "Obligation",
                "properties": {
                    "subject": ob.subject, "action": ob.action, "object": ob.object,
                    "modality": ob.modality, "compliance_category": ob.compliance_category,
                    "confidence_score": ob.confidence_score or 0.0
                }
            })
            edges.append({
                "source": str(cl.id),
                "target": str(ob.id),
                "type": "HAS_OBLIGATION",
                "properties": {}
            })

            # Fetch regulatory mappings
            mappings = db.scalars(select(RegulatoryMapping).where(RegulatoryMapping.obligation_id == ob.id, RegulatoryMapping.deleted_at.is_(None))).all()
            for mp in mappings:
                if mp.framework_name != "NONE":
                    reg_key = f"{mp.framework_name}_{mp.clause_number}"
                    # Add Regulation node if not already added
                    if not any(n["id"] == reg_key for n in nodes):
                        nodes.append({
                            "id": reg_key,
                            "label": mp.clause_number,
                            "type": "Regulation",
                            "properties": {"framework_name": mp.framework_name, "clause_reference": mp.clause_number, "explanation": mp.ai_explanation}
                        })
                    edges.append({
                        "source": str(ob.id),
                        "target": reg_key,
                        "type": "MAPS_TO",
                        "properties": {"confidence_score": mp.confidence_score}
                    })

    return {"nodes": nodes, "edges": edges}


@router.get(
    "/obligation/{obligation_id}",
    response_model=GraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve obligation graph slice"
)
def get_obligation_graph(
    obligation_id: uuid.UUID,
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """Retrieves graph slice centered around a single obligation node."""
    nodes = []
    edges = []

    # 1. Attempt Neo4j query
    if neo4j and neo4j.verify_connectivity():
        try:
            with neo4j.get_session() as session:
                result = session.run(
                    """
                    MATCH (o:Obligation {id: $ob_id})
                    OPTIONAL MATCH (c:Clause)-[r1:HAS_OBLIGATION]->(o)
                    OPTIONAL MATCH (o)-[r2:MAPS_TO]->(reg:Regulation)
                    OPTIONAL MATCH (o)-[r3:HAS_FINDING]->(f:Finding)
                    RETURN o, r1, c, r2, reg, r3, f
                    """,
                    ob_id=str(obligation_id)
                )

                visited = set()
                for record in result:
                    for key in ["o", "c", "reg", "f"]:
                        node = record.get(key)
                        if node and node.element_id not in visited:
                            visited.add(node.element_id)
                            node_type = list(node.labels)[0] if node.labels else "Unknown"
                            nodes.append({
                                "id": node.get("id") or node.get("framework_name") + "_" + node.get("clause_reference", ""),
                                "label": node.get("title") or node.get("clause_number") or node.get("subject") or node.get("clause_reference") or "Node",
                                "type": node_type,
                                "properties": dict(node)
                            })
                    for key in ["r1", "r2", "r3"]:
                        rel = record.get(key)
                        if rel:
                            src_node = rel.start_node
                            tgt_node = rel.end_node
                            edges.append({
                                "source": src_node.get("id") or src_node.get("framework_name") + "_" + src_node.get("clause_reference", ""),
                                "target": tgt_node.get("id") or tgt_node.get("framework_name") + "_" + tgt_node.get("clause_reference", ""),
                                "type": rel.type,
                                "properties": dict(rel)
                            })
            if nodes:
                return {"nodes": nodes, "edges": edges}
        except Exception as exc:
            logger.error("Neo4j obligation graph traversal failed: %s", exc)

    # 2. SQL Fallback
    ob = db.get(Obligation, obligation_id)
    if not ob:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Obligation with ID '{obligation_id}' not found."
        )

    nodes.append({
        "id": str(ob.id),
        "label": ob.subject or "Obligation",
        "type": "Obligation",
        "properties": {"subject": ob.subject, "action": ob.action, "object": ob.object}
    })

    # Add Clause parent node
    clause = db.get(Clause, ob.clause_id)
    if clause:
        nodes.append({
            "id": str(clause.id),
            "label": clause.clause_number or "Clause",
            "type": "Clause",
            "properties": {"clause_number": clause.clause_number}
        })
        edges.append({
            "source": str(clause.id),
            "target": str(ob.id),
            "type": "HAS_OBLIGATION",
            "properties": {}
        })

    # Add mappings
    mappings = db.scalars(select(RegulatoryMapping).where(RegulatoryMapping.obligation_id == ob.id, RegulatoryMapping.deleted_at.is_(None))).all()
    for mp in mappings:
        if mp.framework_name != "NONE":
            reg_key = f"{mp.framework_name}_{mp.clause_number}"
            nodes.append({
                "id": reg_key,
                "label": mp.clause_number or "Regulation",
                "type": "Regulation",
                "properties": {"framework_name": mp.framework_name, "clause_reference": mp.clause_number}
            })
            edges.append({
                "source": str(ob.id),
                "target": reg_key,
                "type": "MAPS_TO",
                "properties": {}
            })

    return {"nodes": nodes, "edges": edges}


@router.get(
    "/policy/{policy_id}/impact",
    response_model=ImpactAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Policy Impact Analysis traversal"
)
def get_policy_impact_analysis(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """Performs graph traversal queries analyzing downstream compliance impact of a policy."""
    # 1. Attempt to query Neo4j
    if neo4j and neo4j.verify_connectivity():
        try:
            with neo4j.get_session() as session:
                # Obligations
                res_obs = session.run(
                    "MATCH (p:Policy {id: $id})-[:HAS_CLAUSE]->(:Clause)-[:HAS_OBLIGATION]->(o:Obligation) RETURN DISTINCT o",
                    id=str(policy_id)
                )
                connected_obs = [dict(record["o"]) for record in res_obs]

                # Regulations
                res_regs = session.run(
                    "MATCH (p:Policy {id: $id})-[:HAS_CLAUSE]->(:Clause)-[:HAS_OBLIGATION]->(:Obligation)-[:MAPS_TO]->(r:Regulation) RETURN DISTINCT r",
                    id=str(policy_id)
                )
                related_regs = [dict(record["r"]) for record in res_regs]

                # Findings
                res_finds = session.run(
                    "MATCH (p:Policy {id: $id})-[:HAS_CLAUSE]->(:Clause)-[:HAS_OBLIGATION]->(:Obligation)-[:HAS_FINDING]->(f:Finding) RETURN DISTINCT f",
                    id=str(policy_id)
                )
                conflicts = [dict(record["f"]) for record in res_finds]

                # Recommendations
                res_recs = session.run(
                    "MATCH (p:Policy {id: $id})-[:HAS_CLAUSE]->(:Clause)-[:HAS_OBLIGATION]->(:Obligation)-[:HAS_FINDING]->(:Finding)-[:HAS_RECOMMENDATION]->(rec:Recommendation) RETURN DISTINCT rec",
                    id=str(policy_id)
                )
                recommendations = [dict(record["rec"]) for record in res_recs]

                # Impacted Policies
                res_pols = session.run(
                    """
                    MATCH (p:Policy {id: $id})-[:HAS_CLAUSE]->(:Clause)-[:HAS_OBLIGATION]->(o1:Obligation)-[:CONFLICTS_WITH]-(o2:Obligation)<-[:HAS_OBLIGATION]-(:Clause)<-[:HAS_CLAUSE]-(p2:Policy)
                    WHERE p2.id <> p.id
                    RETURN DISTINCT p2
                    """,
                    id=str(policy_id)
                )
                impacted_pols = [dict(record["p2"]) for record in res_pols]

                return {
                    "connected_obligations": connected_obs,
                    "related_regulations": related_regs,
                    "conflicts": conflicts,
                    "recommendations": recommendations,
                    "impacted_policies": impacted_pols
                }
        except Exception as exc:
            logger.error("Neo4j policy impact traversal failed: %s", exc)

    # 2. SQL Fallback
    logger.info("Executing SQL fallback traversal queries for policy impact analysis.")
    policy = db.get(Policy, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    clauses = db.scalars(select(Clause).where(Clause.policy_id == policy_id, Clause.deleted_at.is_(None))).all()
    clause_ids = [c.id for c in clauses]

    obligations = []
    if clause_ids:
        obligations = db.scalars(select(Obligation).where(Obligation.clause_id.in_(clause_ids), Obligation.deleted_at.is_(None))).all()
    
    obligation_ids = [ob.id for ob in obligations]

    # Regulations mapped
    related_regs = []
    if obligation_ids:
        mappings = db.scalars(select(RegulatoryMapping).where(RegulatoryMapping.obligation_id.in_(obligation_ids), RegulatoryMapping.deleted_at.is_(None))).all()
        for mp in mappings:
            if mp.framework_name != "NONE":
                related_regs.append({
                    "framework_name": mp.framework_name,
                    "clause_reference": mp.clause_number,
                    "title": mp.clause_number,
                    "explanation": mp.ai_explanation
                })

    # Conflicts / Findings
    conflicts_list = []
    recs_list = []
    impacted_policies = []

    if obligation_ids:
        conflicts = db.scalars(
            select(Conflict).where(
                or_(Conflict.source_obligation_id.in_(obligation_ids), Conflict.target_obligation_id.in_(obligation_ids)),
                Conflict.deleted_at.is_(None)
            )
        ).all()

        for conf in conflicts:
            conflicts_list.append({
                "id": str(conf.id),
                "type": conf.conflict_type or "CONFLICT",
                "severity": conf.severity,
                "explanation": conf.ai_explanation
            })

            # Fetch recommendations
            recs = db.scalars(select(Recommendation).where(Recommendation.conflict_id == conf.id, Recommendation.deleted_at.is_(None))).all()
            for r in recs:
                recs_list.append({
                    "id": str(r.id),
                    "suggested_action": r.suggested_action,
                    "revised_clause": r.revised_clause,
                    "status": r.status
                })

            # Check impacted policy
            other_pol_id = conf.target_policy_id if conf.source_policy_id == policy_id else conf.source_policy_id
            if other_pol_id and other_pol_id != policy_id:
                other_pol = db.get(Policy, other_pol_id)
                if other_pol and not any(p["id"] == str(other_pol.id) for p in impacted_policies):
                    impacted_policies.append({
                        "id": str(other_pol.id),
                        "title": other_pol.title,
                        "status": other_pol.status
                    })

    return {
        "connected_obligations": [{"id": str(ob.id), "subject": ob.subject, "action": ob.action, "object": ob.object} for ob in obligations],
        "related_regulations": related_regs,
        "conflicts": conflicts_list,
        "recommendations": recs_list,
        "impacted_policies": impacted_policies
    }


@router.get(
    "/search",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
    summary="Search nodes in Neo4j Knowledge Graph"
)
def search_graph(
    q: str = Query(..., description="Query term to search for"),
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """Searches for nodes inside the Knowledge Graph match parameters."""
    if neo4j and neo4j.verify_connectivity():
        try:
            with neo4j.get_session() as session:
                res = session.run(
                    """
                    MATCH (n)
                    WHERE n.title CONTAINS $q OR n.subject CONTAINS $q OR n.clause_number CONTAINS $q OR n.framework_name CONTAINS $q
                    RETURN n LIMIT 25
                    """,
                    q=q
                )
                nodes = []
                for record in res:
                    node = record["n"]
                    node_type = list(node.labels)[0] if node.labels else "Unknown"
                    nodes.append({
                        "id": node.get("id") or node.get("framework_name") + "_" + node.get("clause_reference", ""),
                        "label": node.get("title") or node.get("clause_number") or node.get("subject") or node.get("clause_reference") or "Node",
                        "type": node_type,
                        "properties": dict(node)
                    })
                return nodes
        except Exception as exc:
            logger.error("Neo4j search failed: %s", exc)

    # SQL Fallback
    logger.info("Executing SQL fallback search for graph query: %s", q)
    results = []
    policies = db.scalars(select(Policy).where(Policy.title.ilike(f"%{q}%"), Policy.deleted_at.is_(None))).all()
    for p in policies:
        results.append({"id": str(p.id), "label": p.title, "type": "Policy", "properties": {"title": p.title}})

    obligations = db.scalars(
        select(Obligation).where(
            or_(Obligation.subject.ilike(f"%{q}%"), Obligation.action.ilike(f"%{q}%"), Obligation.object.ilike(f"%{q}%")),
            Obligation.deleted_at.is_(None)
        )
    ).all()
    for ob in obligations:
        results.append({"id": str(ob.id), "label": ob.subject, "type": "Obligation", "properties": {"subject": ob.subject}})

    mappings = db.scalars(
        select(RegulatoryMapping).where(
            or_(RegulatoryMapping.framework_name.ilike(f"%{q}%"), RegulatoryMapping.clause_number.ilike(f"%{q}%")),
            RegulatoryMapping.deleted_at.is_(None)
        )
    ).all()
    for mp in mappings:
        if mp.framework_name != "NONE":
            reg_key = f"{mp.framework_name}_{mp.clause_number}"
            if not any(r["id"] == reg_key for r in results):
                results.append({
                    "id": reg_key,
                    "label": mp.clause_number,
                    "type": "Regulation",
                    "properties": {"framework_name": mp.framework_name, "clause_reference": mp.clause_number}
                })

    return results
