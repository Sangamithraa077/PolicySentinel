"""Service for synchronizing PostgreSQL policy metadata, clauses, obligations, and findings to Neo4j Graph."""
from __future__ import annotations

import logging
import uuid
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from backend.graph.neo4j_client import Neo4jClient
from backend.models.policy import Policy
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.regulatory_mapping import RegulatoryMapping
from backend.models.regulatory_clause import RegulatoryClause
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation

logger = logging.getLogger(__name__)


class GraphPopulationService:
    def __init__(self, db: Session, neo4j_client: Neo4jClient | None = None) -> None:
        self._db = db
        self._neo4j = neo4j_client or Neo4jClient()

    def initialize_constraints(self) -> None:
        """Initializes schema constraints and indices inside Neo4j database."""
        logger.info("Initializing Neo4j schema constraints...")
        queries = [
            "CREATE CONSTRAINT UNIQUE_POLICY_ID IF NOT EXISTS FOR (p:Policy) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT UNIQUE_CLAUSE_ID IF NOT EXISTS FOR (c:Clause) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT UNIQUE_OBLIGATION_ID IF NOT EXISTS FOR (o:Obligation) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT UNIQUE_FINDING_ID IF NOT EXISTS FOR (f:Finding) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT UNIQUE_RECOMMENDATION_ID IF NOT EXISTS FOR (r:Recommendation) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT UNIQUE_REGULATION IF NOT EXISTS FOR (reg:Regulation) REQUIRE (reg.framework_name, reg.clause_reference) IS UNIQUE"
        ]

        with self._neo4j.get_session() as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception as exc:
                    logger.warning("Constraint creation command ignored (expected behavior on some Neo4j editions): %s", exc)

    def sync_policy(self, policy_id: uuid.UUID) -> bool:
        """Reads policy structure, obligations, mappings, findings, and recommendations from DB and synchronizes to Neo4j in optimized batches."""
        logger.info("Starting optimized graph synchronization for Policy ID: %s", policy_id)
        
        policy = self._db.get(Policy, policy_id)
        if not policy:
            logger.error("Sync failed: Policy %s not found in Postgres.", policy_id)
            return False

        # Initialize constraints first
        self.initialize_constraints()

        try:
            # 1. Single-roundtrip SQL queries to fetch all related structures
            clauses = self._db.scalars(
                select(Clause).where(
                    Clause.policy_id == policy_id,
                    Clause.deleted_at.is_(None)
                )
            ).all()

            if not clauses:
                logger.info("No clauses found for policy %s. Graph sync done.", policy_id)
                return True

            clause_ids = [cl.id for cl in clauses]
            obligations = self._db.scalars(
                select(Obligation).where(
                    Obligation.clause_id.in_(clause_ids),
                    Obligation.deleted_at.is_(None)
                )
            ).all()

            obligation_ids = [ob.id for ob in obligations]
            
            mappings = []
            if obligation_ids:
                mappings = self._db.scalars(
                    select(RegulatoryMapping).where(
                        RegulatoryMapping.obligation_id.in_(obligation_ids),
                        RegulatoryMapping.deleted_at.is_(None)
                    )
                ).all()

            conflicts = []
            if obligation_ids:
                conflicts = self._db.scalars(
                    select(Conflict).where(
                        or_(
                            Conflict.source_obligation_id.in_(obligation_ids),
                            Conflict.target_obligation_id.in_(obligation_ids)
                        ),
                        Conflict.deleted_at.is_(None)
                    )
                ).all()

            conflict_ids = [c.id for c in conflicts]
            recs = []
            if conflict_ids:
                recs = self._db.scalars(
                    select(Recommendation).where(
                        Recommendation.conflict_id.in_(conflict_ids),
                        Recommendation.deleted_at.is_(None)
                    )
                ).all()

            # 2. Batch write to Neo4j Graph database
            with self._neo4j.get_session() as session:
                # Sync Policy node
                session.run(
                    """
                    MERGE (p:Policy {id: $id})
                    SET p.title = $title, p.status = $status, p.created_at = $created_at
                    """,
                    id=str(policy.id),
                    title=policy.title,
                    status=policy.status,
                    created_at=policy.created_at.isoformat() if policy.created_at else ""
                )

                # Batch Sync Clause nodes & relations
                if clauses:
                    session.run(
                        """
                        UNWIND $clauses AS cl
                        MERGE (c:Clause {id: cl.id})
                        SET c.clause_number = cl.clause_number, c.text = cl.text, c.order_index = cl.order_index
                        WITH c, cl
                        MATCH (p:Policy {id: cl.policy_id})
                        MERGE (p)-[:HAS_CLAUSE]->(c)
                        """,
                        clauses=[{
                            "id": str(cl.id),
                            "clause_number": cl.clause_number,
                            "text": cl.text,
                            "order_index": cl.order_index,
                            "policy_id": str(policy_id)
                        } for cl in clauses]
                    )

                # Batch Sync Obligation nodes & relations
                if obligations:
                    session.run(
                        """
                        UNWIND $obs AS ob
                        MERGE (o:Obligation {id: ob.id})
                        SET o.subject = ob.subject, o.action = ob.action, o.object = ob.object, 
                            o.modality = ob.modality, o.compliance_category = ob.compliance_category,
                            o.confidence_score = ob.confidence_score
                        WITH o, ob
                        MATCH (c:Clause {id: ob.clause_id})
                        MERGE (c)-[:HAS_OBLIGATION]->(o)
                        """,
                        obs=[{
                            "id": str(ob.id),
                            "subject": ob.subject,
                            "action": ob.action,
                            "object": ob.object,
                            "modality": ob.modality,
                            "compliance_category": ob.compliance_category,
                            "confidence_score": ob.confidence_score or 0.0,
                            "clause_id": str(ob.clause_id)
                        } for ob in obligations]
                    )

                # Batch Sync Regulations & MAPS_TO relations
                reg_mappings = [m for m in mappings if m.framework_name != "NONE"]
                if reg_mappings:
                    session.run(
                        """
                        UNWIND $maps AS mp
                        MERGE (r:Regulation {framework_name: mp.framework_name, clause_reference: mp.clause_reference})
                        SET r.title = mp.title
                        WITH r, mp
                        MATCH (o:Obligation {id: mp.obligation_id})
                        MERGE (o)-[:MAPS_TO {confidence_score: mp.confidence_score, explanation: mp.explanation}]->(r)
                        """,
                        maps=[{
                            "framework_name": m.framework_name,
                            "clause_reference": m.clause_number,
                            "title": m.clause_number,
                            "obligation_id": str(m.obligation_id),
                            "confidence_score": m.confidence_score or 0.0,
                            "explanation": m.ai_explanation or ""
                        } for m in reg_mappings]
                    )

                # Batch Sync Finding nodes
                if conflicts:
                    findings_data = []
                    for conf in conflicts:
                        finding_type = (conf.relationship_type or "CONFLICT").upper()
                        findings_data.append({
                            "id": str(conf.id),
                            "type": finding_type,
                            "severity": conf.severity or "medium",
                            "explanation": conf.ai_explanation or "",
                            "confidence_score": conf.confidence_score or 0.0
                        })

                    session.run(
                        """
                        UNWIND $findings AS f_data
                        MERGE (f:Finding {id: f_data.id})
                        SET f.type = f_data.type, f.severity = f_data.severity, f.explanation = f_data.explanation,
                            f.confidence_score = f_data.confidence_score
                        """,
                        findings=findings_data
                    )

                    # Batch Sync Finding connections & direct semantic links
                    for conf in conflicts:
                        finding_type = (conf.relationship_type or "CONFLICT").upper()
                        rel_type = "CONFLICTS_WITH"
                        if finding_type == "REDUNDANT":
                            rel_type = "REDUNDANT_WITH"
                        elif finding_type == "COMPLEMENTARY":
                            rel_type = "COMPLEMENTS"
                        elif finding_type == "UNRELATED":
                            rel_type = "RELATED_TO"

                        if conf.source_obligation_id:
                            session.run(
                                """
                                MATCH (o:Obligation {id: $ob_id}), (f:Finding {id: $f_id})
                                MERGE (o)-[:HAS_FINDING]->(f)
                                """,
                                ob_id=str(conf.source_obligation_id),
                                f_id=str(conf.id)
                            )
                        if conf.target_obligation_id:
                            session.run(
                                """
                                MATCH (o:Obligation {id: $ob_id}), (f:Finding {id: $f_id})
                                MERGE (o)-[:HAS_FINDING]->(f)
                                """,
                                ob_id=str(conf.target_obligation_id),
                                f_id=str(conf.id)
                            )
                        if conf.source_obligation_id and conf.target_obligation_id:
                            session.run(
                                f"""
                                MATCH (o1:Obligation {{id: $src_id}}), (o2:Obligation {{id: $tgt_id}})
                                MERGE (o1)-[r:{rel_type}]->(o2)
                                SET r.similarity_score = $similarity_score, r.explanation = $explanation
                                """,
                                src_id=str(conf.source_obligation_id),
                                tgt_id=str(conf.target_obligation_id),
                                similarity_score=conf.similarity_score or 0.0,
                                explanation=conf.ai_explanation or ""
                            )

                # Batch Sync Recommendations
                if recs:
                    session.run(
                        """
                        UNWIND $recs AS rc_data
                        MERGE (r:Recommendation {id: rc_data.id})
                        SET r.suggested_action = rc_data.suggested_action, r.revised_clause = rc_data.revised_clause,
                            r.status = rc_data.status, r.confidence_score = rc_data.confidence_score
                        WITH r, rc_data
                        MATCH (f:Finding {id: rc_data.finding_id})
                        MERGE (f)-[:HAS_RECOMMENDATION]->(r)
                        """,
                        recs=[{
                            "id": str(rc.id),
                            "suggested_action": rc.suggested_action,
                            "revised_clause": rc.revised_clause or "",
                            "status": rc.status,
                            "confidence_score": rc.confidence_score or 0.0,
                            "finding_id": str(rc.conflict_id)
                        } for rc in recs]
                    )

            logger.info("Successfully completed optimized graph synchronization for Policy ID: %s", policy_id)
            return True
        except Exception as exc:
            logger.error("Failed to populate Neo4j graph for Policy ID %s: %s", policy_id, exc)
            return False

    def sync_all(self) -> int:
        """Synchronizes all non-deleted policies from PostgreSQL to Neo4j graph database."""
        logger.info("Starting bulk PostgreSQL to Neo4j graph synchronization...")
        policies = self._db.scalars(select(Policy).where(Policy.deleted_at.is_(None))).all()
        
        success_count = 0
        for p in policies:
            if self.sync_policy(p.id):
                success_count += 1

        logger.info("Bulk synchronization completed. Synced %s/%s policies.", success_count, len(policies))
        return success_count
