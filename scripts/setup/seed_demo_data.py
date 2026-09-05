"""Seed script to populate PostgreSQL and Neo4j database with realistic enterprise demo data.

Generates:
- 5 Companies
- 15 Policies
- 100+ Clauses
- 150+ Obligations
- Conflicts, Redundancy, and Complementary findings
- Regulatory mappings (to GDPR, ISO 27001, RBI, SEBI)
- Recommendations

Usage:
    python scripts/setup/seed_demo_data.py
"""
from __future__ import annotations

import sys
import uuid
import random
from pathlib import Path
from datetime import datetime, date, timedelta, timezone

# Root the repository path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import bcrypt
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.database.session import SessionLocal

from backend.models.company import Company
from backend.models.user import User
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.regulatory_mapping import RegulatoryMapping
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation
from backend.models.enums import PolicyDocumentFileType, PolicyStatus, PolicyVersionStatus, UserRole
from backend.services.regulatory_knowledge_base_service import RegulatoryKnowledgeBaseService
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.graph_population_service import GraphPopulationService


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def seed_demo_data():
    db: Session = SessionLocal()
    print("[Seed] Wiping existing relational database tables...")
    try:
        db.execute(text("TRUNCATE TABLE companies, users, policies, policy_versions, clauses, obligations, regulatory_mappings, conflicts, recommendations, compliance_audit_logs CASCADE;"))
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[Seed] Truncate failed, proceeding to append rows: {exc}")

    # Seed standard external regulations
    print("[Seed] Seeding Regulatory Knowledge Base...")
    kb_service = RegulatoryKnowledgeBaseService(db)
    kb_service.seed_default_frameworks()

    # 1. Create 5 Companies
    print("[Seed] Creating 5 companies...")
    companies = []
    company_names = [
        "Société Générale",
        "Société Générale (Compliance & Ethics)",
        "Société Générale (Information Security)",
        "Société Générale (Global Solution Centre)",
        "Société Générale (Corporate & Investment Banking)",
    ]
    for name in company_names:
        co = Company(name=name)
        db.add(co)
        companies.append(co)
    db.flush()

    # Create Users
    print("[Seed] Creating administrative users...")
    password_val = hash_password("DemoPassword123!")
    users = []
    for co in companies:
        slug = co.name.lower().replace(' ', '').replace('(', '').replace(')', '').replace('&', 'and').replace('é', 'e')[:20]
        admin_user = User(
            company_id=co.id,
            email=f"compliance@{slug}.com",
            password_hash=password_val,
            full_name="Compliance Officer",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        users.append(admin_user)
    db.flush()

    # 2. Create 15 Policies (3 per company)
    print("[Seed] Creating 15 policies...")
    policy_templates = [
        ("Information Security Policy", "Specifies system logging, access controls, and data protection rules."),
        ("Data Privacy & Subjects Rights Policy", "Defines user consent, data retention, and subject erasure timelines."),
        ("Operational Risk Management Policy", "Outlines business continuity plans and regulatory incident reporting rules.")
    ]

    all_policies = []
    all_clauses = []
    all_obligations = []

    for co_idx, co in enumerate(companies):
        uploader = users[co_idx]
        for p_idx, (title, desc) in enumerate(policy_templates):
            pol = Policy(
                company_id=co.id,
                title=f"{co.name} - {title}",
                status=PolicyStatus.ACTIVE
            )
            db.add(pol)
            db.flush()

            ver = PolicyVersion(
                policy_id=pol.id,
                version_number=1,
                source_file_reference=f"uploads/policies/{pol.id}_v1.pdf",
                file_hash=f"hash-{pol.id}",
                uploaded_by_user_id=uploader.id,
                status=PolicyVersionStatus.PUBLISHED,
                original_filename=f"{title.replace(' ', '_').lower()}.pdf",
                size_bytes=4096,
                file_type=PolicyDocumentFileType.PDF,
                description=desc,
                uploaded_at=datetime.utcnow() - timedelta(days=200),
                extracted_text="Placeholder policy extraction content."
            )
            ver.effective_date = date.today() - timedelta(days=200)
            pol.current_version = ver
            db.add(ver)
            db.flush()
            all_policies.append(pol)

            # Generate ~7 clauses per policy (Totaling ~105 clauses)
            for c_idx in range(1, 8):
                clause_text = ""
                clause_num = f"{p_idx + 1}.{c_idx}"
                
                # Make text content realistic based on policy type
                if "Security" in title:
                    if c_idx == 1:
                        clause_text = "All system access attempts must be recorded in local event log files."
                    elif c_idx == 2:
                        clause_text = "The IT administrator shall perform hardware asset inventories monthly."
                    elif c_idx == 3:
                        clause_text = "User access controls should review permission configurations quarterly."
                    elif c_idx == 4:
                        clause_text = "System log data files must be protected against unauthorized read access."
                    else:
                        clause_text = f"General security guideline clause text for subsection reference {clause_num}."
                elif "Privacy" in title:
                    if c_idx == 1:
                        clause_text = "The privacy office shall erase personal user data within 30 days of subject requests."
                    elif c_idx == 2:
                        clause_text = "Personal details records may be archived for transaction auditing reasons."
                    elif c_idx == 3:
                        clause_text = "User consent logs should be retained in the active compliance DB for 5 years."
                    elif c_idx == 4:
                        clause_text = "No user identification details shall be stored in external files."
                    else:
                        clause_text = f"General privacy guideline clause text for subsection reference {clause_num}."
                else:
                    if c_idx == 1:
                        clause_text = "Disclosures of material corporate events must occur within 24 hours of decision."
                    elif c_idx == 2:
                        clause_text = "Customer Due Diligence identity documents are verified upon account creation."
                    elif c_idx == 3:
                        clause_text = "Corporate business logs will undergo operational audits annually."
                    else:
                        clause_text = f"General operational risk clause text for subsection reference {clause_num}."

                cl = Clause(
                    policy_id=pol.id,
                    policy_version_id=ver.id,
                    clause_number=clause_num,
                    text=clause_text,
                    order_index=c_idx
                )
                db.add(cl)
                db.flush()
                all_clauses.append(cl)

                # Generate 1 to 2 obligations per clause (Totaling ~150+ obligations)
                subjects = ["IT administrator", "Privacy office", "Compliance team", "System control", "Operational unit"]
                modalities = ["Must", "Shall", "Should", "May"]
                categories = ["Security", "Privacy", "Financial", "Operational"]
                
                # Make first obligation highly realistic matching the clause text
                mod = "Must" if "must" in clause_text.lower() else ("Shall" if "shall" in clause_text.lower() else ("Should" if "should" in clause_text.lower() else "May"))
                subject = "System logs"
                for sb in subjects:
                    if sb.split(" ")[0].lower() in clause_text.lower():
                        subject = sb
                        break
                        
                ob1 = Obligation(
                    clause_id=cl.id,
                    policy_id=pol.id,
                    subject=subject,
                    action="record event activity" if "log" in clause_text.lower() else ("erase subject data" if "erase" in clause_text.lower() else "perform compliance reviews"),
                    object="log files" if "log" in clause_text.lower() else ("user requests" if "erase" in clause_text.lower() else "standard operations"),
                    modality=mod,
                    compliance_category="Security" if "Security" in title else ("Privacy" if "Privacy" in title else "Operational"),
                    confidence_score=0.95,
                    ai_model="mock"
                )
                db.add(ob1)
                db.flush()
                all_obligations.append(ob1)

                # Generate second helper obligation for 50% of clauses to exceed 150 total obligations
                if c_idx % 2 == 0:
                    ob2 = Obligation(
                        clause_id=cl.id,
                        policy_id=pol.id,
                        subject=random.choice(subjects),
                        action="validate and store configuration",
                        object="compliance parameter updates",
                        modality=random.choice(modalities),
                        compliance_category=random.choice(categories),
                        confidence_score=0.90,
                        ai_model="mock"
                    )
                    db.add(ob2)
                    db.flush()
                    all_obligations.append(ob2)

    # 3. Create Regulatory Mappings
    print("[Seed] Seeding regulatory mappings...")
    for ob in all_obligations:
        text_to_search = f"{ob.subject} {ob.action} {ob.object}".lower()
        framework = "NONE"
        clause_ref = "NONE"
        confidence = 0.0
        explanation = "No matching regulatory guideline identified."

        if "log" in text_to_search:
            framework = "ISO 27001"
            clause_ref = "A.12.4.1"
            confidence = 0.95
            explanation = "Seeded match to Event logging."
        elif "erase" in text_to_search:
            framework = "GDPR"
            clause_ref = "Article 17(1)"
            confidence = 0.92
            explanation = "Seeded match to Right to Erasure."
        elif "consent" in text_to_search:
            framework = "GDPR"
            clause_ref = "Article 32"
            confidence = 0.88
            explanation = "Seeded match to user data security consent."

        mapping = RegulatoryMapping(
            policy_id=ob.policy_id,
            obligation_id=ob.id,
            framework_name=framework,
            regulation_id=clause_ref,
            clause_number=clause_ref,
            confidence_score=confidence,
            ai_explanation=explanation
        )
        db.add(mapping)
    db.flush()

    # 4. Create Findings & Conflicts
    # (Contradictions, Redundancies, and Complementary relationships)
    print("[Seed] Seeding findings and conflicts...")
    findings = []
    
    # Locate obligations from same company but different policies to link
    for co in companies:
        co_obs = [o for o in all_obligations if o.policy_id in [p.id for p in all_policies if p.company_id == co.id]]
        if len(co_obs) < 4:
            continue
            
        # 4.1 Contradicting Conflict (e.g. Ob 1 logs always, Ob 2 logs never)
        ob_a = co_obs[0]
        ob_b = co_obs[1]
        
        conflict = Conflict(
            source_policy_id=ob_a.policy_id,
            target_policy_id=ob_b.policy_id,
            source_obligation_id=ob_a.id,
            target_obligation_id=ob_b.id,
            conflict_type="contradiction",
            relationship_type="CONFLICT",
            similarity_score=0.88,
            severity="high",
            ai_explanation="Contradicting modalities detected between log rules.",
            status="Open"
        )
        db.add(conflict)
        db.flush()
        findings.append(conflict)

        # Approved recommendation offsetting the conflict
        rec = Recommendation(
            conflict_id=conflict.id,
            recommendation_summary="Harmonize system log requirements.",
            suggested_action="Ensure all transaction details are recorded.",
            original_clause=ob_b.action,
            revised_clause="Standardize log outputs.",
            reason="Alignment to framework rules",
            ai_model="mock",
            confidence_score=0.92,
            status="Approved",
            reviewer_name="Ava compliance officer",
            reviewed_at=datetime.now()
        )
        db.add(rec)

        # 4.2 Redundant findings
        ob_c = co_obs[2]
        ob_d = co_obs[3]
        redundancy = Conflict(
            source_policy_id=ob_c.policy_id,
            target_policy_id=ob_d.policy_id,
            source_obligation_id=ob_c.id,
            target_obligation_id=ob_d.id,
            conflict_type="redundancy",
            relationship_type="REDUNDANT",
            similarity_score=0.95,
            severity="low",
            ai_explanation="Obligations perform duplicate compliance actions.",
            status="Open"
        )
        db.add(redundancy)
        db.flush()
        findings.append(redundancy)

        # 4.3 Complementary findings
        if len(co_obs) >= 6:
            ob_e = co_obs[4]
            ob_f = co_obs[5]
            complementary = Conflict(
                source_policy_id=ob_e.policy_id,
                target_policy_id=ob_f.policy_id,
                source_obligation_id=ob_e.id,
                target_obligation_id=ob_f.id,
                conflict_type="complementary",
                relationship_type="COMPLEMENTARY",
                similarity_score=0.82,
                severity="low",
                ai_explanation="Obligations reinforce data verification cycles.",
                status="Resolved"
            )
            db.add(complementary)
            db.flush()
            findings.append(complementary)

    db.commit()
    print(f"[Seed] Successfully seeded {len(companies)} Companies, {len(all_policies)} Policies, {len(all_clauses)} Clauses, {len(all_obligations)} Obligations, and findings in PostgreSQL.")

    # 5. Populate Neo4j Knowledge Graph
    print("[Seed] Connecting to Neo4j database to trigger Graph synchronization...")
    try:
        neo4j_client = Neo4jClient()
        if neo4j_client.verify_connectivity():
            sync_service = GraphPopulationService(db, neo4j_client=neo4j_client)
            sync_service.initialize_constraints()
            synced_count = sync_service.sync_all()
            print(f"[Seed] Successfully populated Neo4j Knowledge Graph. Synced {synced_count} policies.")
        else:
            print("[Seed] Neo4j is offline. Skipping Neo4j sync. API SQL fallback remains active for the UI.")
    except Exception as graph_err:
        print(f"[Seed] Failed to populate Neo4j: {graph_err}. Traversal fallbacks remain available.")
        
    db.close()
    print("[Seed] Seeding completed.")


if __name__ == "__main__":
    seed_demo_data()
