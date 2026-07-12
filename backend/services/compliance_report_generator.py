"""Service class generating highly professional PDF compliance reports using PyMuPDF (fitz)."""

from __future__ import annotations

import io
import uuid
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

import fitz  # PyMuPDF

from backend.models.policy import Policy
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation
from backend.models.compliance_audit_log import ComplianceAuditLog
from backend.services.compliance_dashboard_service import ComplianceDashboardService

logger = logging.getLogger(__name__)


class ComplianceReportGenerator:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._dashboard_service = ComplianceDashboardService(db)

    def generate_report(self, company_id: uuid.UUID) -> bytes:
        """Generates a downloadable PDF report detailing compliance health, conflicts, and audit trail logs."""
        # 1. Fetch data
        summary = self._dashboard_service.get_executive_summary(company_id)
        
        policies_query = select(Policy).where(
            Policy.company_id == company_id,
            Policy.deleted_at.is_(None)
        )
        policies = self._db.scalars(policies_query).all()
        policy_ids = [p.id for p in policies]

        conflicts = []
        recommendations = []
        if policy_ids:
            conflicts_query = select(Conflict).where(
                Conflict.target_policy_id.in_(policy_ids),
                Conflict.deleted_at.is_(None)
            )
            conflicts = self._db.scalars(conflicts_query).all()
            conflict_ids = [c.id for c in conflicts]
            if conflict_ids:
                recs_query = select(Recommendation).where(
                    Recommendation.conflict_id.in_(conflict_ids),
                    Recommendation.deleted_at.is_(None)
                )
                recommendations = self._db.scalars(recs_query).all()

        audit_logs, _ = self._dashboard_service.list_audit_history(company_id, limit=15)

        # 2. Build PDF Document
        doc = fitz.open()

        # ========================================== PAGE 1: COVER & EXECUTIVE SUMMARY
        page1 = doc.new_page(width=595, height=842)
        
        # Header Banner
        page1.draw_rect(fitz.Rect(0, 0, 595, 80), color=(0.0, 0.25, 0.45), fill=(0.0, 0.25, 0.45))
        page1.insert_text(fitz.Point(30, 48), "PolicySentinel", fontsize=24, color=(1, 1, 1), fontname="hebo")
        page1.insert_text(fitz.Point(360, 46), "COMPLIANCE INTEGRITY REPORT", fontsize=12, color=(0.8, 0.9, 1.0), fontname="hebo")

        # Report Metadata
        page1.insert_text(fitz.Point(30, 110), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fontsize=9, fontname="heit")
        page1.insert_text(fitz.Point(30, 125), f"Company ID: {company_id}", fontsize=9, fontname="heit")
        
        # Compliance Score Section
        page1.draw_rect(fitz.Rect(30, 150, 565, 230), color=(0.9, 0.92, 0.95), fill=(0.96, 0.97, 0.98), width=1)
        page1.insert_text(fitz.Point(50, 180), "EXECUTIVE SUMMARY", fontsize=14, color=(0.0, 0.25, 0.45), fontname="hebo")
        
        # Score circular display
        score_val = summary["compliance_score"]
        page1.insert_text(fitz.Point(50, 220), f"Compliance Score: {score_val} / 100", fontsize=18, fontname="hebo")
        page1.insert_text(fitz.Point(50, 245), f"Risk Level: {summary['risk_level']}", fontsize=14, fontname="hebo", color=(0.8, 0.1, 0.1) if score_val < 80 else (0.1, 0.6, 0.1))
        
        # Risk summary text wrapper
        risk_text = summary["risk_summary"]
        page1.insert_textbox(fitz.Rect(50, 270, 530, 360), risk_text, fontsize=10, fontname="helv")

        # Metrics Card Grid
        page1.insert_text(fitz.Point(30, 410), "COMPLIANCE INVENTORY STATS", fontsize=12, color=(0.0, 0.25, 0.45), fontname="hebo")
        
        metrics = [
            ("Total Policies", str(summary["total_policies"])),
            ("Total Clauses", str(summary["total_clauses"])),
            ("Total Obligations", str(summary["total_obligations"])),
            ("Active Conflicts", str(summary["active_conflicts"])),
            ("Resolved Conflicts", str(summary["resolved_conflicts"])),
            ("Pending Actions", str(summary["pending_recommendations"]))
        ]

        # Draw metrics grid boxes (3 columns x 2 rows)
        x_starts = [30, 218, 406]
        y_starts = [430, 510]
        card_w, card_h = 160, 65

        for i, (label, val) in enumerate(metrics):
            col = i % 3
            row = i // 3
            x = x_starts[col]
            y = y_starts[row]
            page1.draw_rect(fitz.Rect(x, y, x + card_w, y + card_h), color=(0.85, 0.85, 0.85), fill=(0.98, 0.98, 0.98), width=1)
            page1.insert_text(fitz.Point(x + 10, y + 20), label, fontsize=9, color=(0.4, 0.4, 0.4), fontname="hebo")
            page1.insert_text(fitz.Point(x + 10, y + 48), val, fontsize=18, color=(0.1, 0.1, 0.1), fontname="hebo")

        # footer page 1
        page1.draw_line(fitz.Point(30, 800), fitz.Point(565, 800), color=(0.8, 0.8, 0.8))
        page1.insert_text(fitz.Point(30, 815), "PolicySentinel - Page 1 of 3", fontsize=8, color=(0.5, 0.5, 0.5))

        # ========================================== PAGE 2: CONFLICTS & RECOMMENDATIONS
        page2 = doc.new_page(width=595, height=842)
        page2.draw_rect(fitz.Rect(0, 0, 595, 50), color=(0.0, 0.25, 0.45), fill=(0.0, 0.25, 0.45))
        page2.insert_text(fitz.Point(30, 30), "PolicySentinel - Conflicts & Recommendations", fontsize=14, color=(1, 1, 1), fontname="hebo")

        y = 80
        page2.insert_text(fitz.Point(30, y), "ACTIVE COMPLIANCE CONFLICTS", fontsize=12, color=(0.0, 0.25, 0.45), fontname="hebo")
        y += 20

        # Draw Conflicts (Limit to first 4 for display, or summary)
        active_conflicts = [c for c in conflicts if c.status != "Resolved"][:4]
        if not active_conflicts:
            page2.insert_text(fitz.Point(30, y), "No active conflicts detected in current policies.", fontsize=10, fontname="heit")
            y += 30
        else:
            for conf in active_conflicts:
                page2.draw_rect(fitz.Rect(30, y, 565, y + 55), color=(0.9, 0.9, 0.9), fill=(0.97, 0.97, 0.98), width=1)
                page2.insert_text(fitz.Point(40, y + 15), f"Conflict ID: {str(conf.id)[:8]}... | Type: {conf.conflict_type.upper()} | Severity: {conf.severity.upper()}", fontsize=9, fontname="hebo")
                
                exp_text = conf.ai_explanation or "No explanation generated."
                page2.insert_textbox(fitz.Rect(40, y + 20, 555, y + 50), exp_text, fontsize=8.5, fontname="helv")
                y += 70

        y += 10
        page2.insert_text(fitz.Point(30, y), "AI RESOLUTION RECOMMENDATIONS", fontsize=12, color=(0.0, 0.25, 0.45), fontname="hebo")
        y += 20

        # Draw Recommendations (Limit to first 3)
        pending_recs = [r for r in recommendations if r.status == "Pending"][:3]
        if not pending_recs:
            page2.insert_text(fitz.Point(30, y), "No pending AI recommendations requiring review.", fontsize=10, fontname="heit")
            y += 30
        else:
            for rec in pending_recs:
                page2.draw_rect(fitz.Rect(30, y, 565, y + 80), color=(0.9, 0.9, 0.9), fill=(0.98, 0.99, 0.98), width=1)
                page2.insert_text(fitz.Point(40, y + 15), f"Recommendation ID: {str(rec.id)[:8]}... | Action: {rec.suggested_action} | Confidence: {rec.confidence_score}", fontsize=9, fontname="hebo", color=(0.1, 0.5, 0.1))
                
                rec_summary = rec.recommendation_summary or "No summary."
                page2.insert_textbox(fitz.Rect(40, y + 22, 555, y + 42), f"Summary: {rec_summary}", fontsize=8.5, fontname="helv")
                
                reason_text = rec.reason or "No reason."
                page2.insert_textbox(fitz.Rect(40, y + 45, 555, y + 75), f"Reason for change: {reason_text}", fontsize=8, fontname="heit", color=(0.3, 0.3, 0.3))
                
                y += 95

        # footer page 2
        page2.draw_line(fitz.Point(30, 800), fitz.Point(565, 800), color=(0.8, 0.8, 0.8))
        page2.insert_text(fitz.Point(30, 815), "PolicySentinel - Page 2 of 3", fontsize=8, color=(0.5, 0.5, 0.5))

        # ========================================== PAGE 3: IMMUTABLE AUDIT TRAIL SUMMARY
        page3 = doc.new_page(width=595, height=842)
        page3.draw_rect(fitz.Rect(0, 0, 595, 50), color=(0.0, 0.25, 0.45), fill=(0.0, 0.25, 0.45))
        page3.insert_text(fitz.Point(30, 30), "PolicySentinel - Immutable Compliance Audit Trail", fontsize=14, color=(1, 1, 1), fontname="hebo")

        y = 80
        page3.insert_text(fitz.Point(30, y), "RECENT PIPELINE COMPLIANCE AUDIT ENTRIES", fontsize=12, color=(0.0, 0.25, 0.45), fontname="hebo")
        y += 20

        # Draw audit table header
        page3.draw_rect(fitz.Rect(30, y, 565, y + 20), color=(0.8, 0.8, 0.8), fill=(0.9, 0.92, 0.95), width=1)
        page3.insert_text(fitz.Point(35, y + 14), "Event Type", fontsize=8.5, fontname="hebo")
        page3.insert_text(fitz.Point(155, y + 14), "User", fontsize=8.5, fontname="hebo")
        page3.insert_text(fitz.Point(265, y + 14), "Timestamp", fontsize=8.5, fontname="hebo")
        page3.insert_text(fitz.Point(385, y + 14), "Description", fontsize=8.5, fontname="hebo")
        y += 20

        # Draw audit logs
        if not audit_logs:
            page3.insert_text(fitz.Point(30, y + 20), "No compliance events logged yet.", fontsize=10, fontname="heit")
        else:
            for log in audit_logs[:12]: # Limit to 12 items on this page
                # Alternate row fills
                fill_color = (0.98, 0.98, 0.99) if y % 40 == 0 else (1.0, 1.0, 1.0)
                page3.draw_rect(fitz.Rect(30, y, 565, y + 30), color=(0.92, 0.92, 0.92), fill=fill_color, width=1)

                page3.insert_text(fitz.Point(35, y + 18), log.event_type[:20], fontsize=8, fontname="hebo")
                page3.insert_text(fitz.Point(155, y + 18), log.user_identifier[:20], fontsize=7.5, fontname="helv")
                page3.insert_text(fitz.Point(265, y + 18), log.occurred_at.strftime("%Y-%m-%d %H:%M"), fontsize=7.5, fontname="helv")
                
                desc_text = log.description or ""
                page3.insert_textbox(fitz.Rect(385, y + 4, 560, y + 26), desc_text, fontsize=7.5, fontname="helv")
                y += 30

        # footer page 3
        page3.draw_line(fitz.Point(30, 800), fitz.Point(565, 800), color=(0.8, 0.8, 0.8))
        page3.insert_text(fitz.Point(30, 815), "PolicySentinel - Page 3 of 3", fontsize=8, color=(0.5, 0.5, 0.5))

        # Save to bytes stream
        stream = io.BytesIO()
        doc.save(stream)
        doc.close()
        
        return stream.getvalue()
