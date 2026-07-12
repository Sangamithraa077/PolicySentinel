import os
import sys
from pathlib import Path

# Root the repository path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import fitz


def draw_wrapped_text(page, text, start_x, start_y, line_height=16, fontsize=10):
    y = start_y
    for line in text.split("\n"):
        page.insert_text((start_x, y), line, fontsize=fontsize)
        y += line_height
    return y


def generate_pdfs():
    demo_dir = REPO_ROOT / "demo-data"
    os.makedirs(demo_dir, exist_ok=True)

    # 1. Generate Information Security Policy v1
    doc_1 = fitz.open()
    page_1 = doc_1.new_page(width=595, height=842) # A4 Size

    policy_1_text = """Information Security Policy v1

Section 1: Endpoint Device Standards
1.1 Laptop Usage: Corporate assets must be accessed using company-managed laptops only. Personal devices are prohibited.
1.2 Local Copying: Local storage of company files on endpoint devices is prohibited to prevent data leakage.

Section 2: Login and Access Controls
2.1 Password Expiration: All passwords must be changed every 90 days to prevent compromised credentials.
2.2 Network Protection: Virtual Private Network (VPN) must always be used when working remotely.

Section 3: Information Governance
3.1 Data Classification: All organizational data must be labeled as public or confidential.
3.2 Log Purging: Audits show system event logs are automatically archived monthly.
3.3 Account Disabling: Disabling user accounts must happen immediately upon employee termination.
"""
    page_1.insert_text((50, 50), "Aether Corporate Standards", fontsize=8, color=(0.5, 0.5, 0.5))
    draw_wrapped_text(page_1, policy_1_text, 50, 100)
    
    pdf_1_path = demo_dir / "Information_Security_Policy_v1.pdf"
    doc_1.save(pdf_1_path)
    doc_1.close()
    print(f"[PDF Gen] Created {pdf_1_path}")

    # 2. Generate Remote Work Policy v2
    doc_2 = fitz.open()
    page_2 = doc_2.new_page(width=595, height=842) # A4 Size

    policy_2_text = """Remote Work Policy v2

Section 1: Flexible Workforce Guidelines
1.1 Device Access: Personal laptops and tablets are allowed to access company resources under supervisor permission.
1.2 Endpoint Storage: Local storage of company files is allowed if the drive is fully encrypted.

Section 2: Credentials and Infrastructure
2.1 Login Credentials: Password changes are required every 180 days.
2.2 Remote Connection: Virtual Private Network (VPN) is recommended when connecting remotely.

Section 3: Information Management
3.1 Data Classification: All organizational data must be labeled as public or confidential.
3.2 Event Archiving: Audits verify server logs are systematically archived monthly.
3.3 IT Offboarding: Return of physical keys and tokens is required during employee offboarding.
"""
    page_2.insert_text((50, 50), "Aether Corporate Standards", fontsize=8, color=(0.5, 0.5, 0.5))
    draw_wrapped_text(page_2, policy_2_text, 50, 100)

    pdf_2_path = demo_dir / "Remote_Work_Policy_v2.pdf"
    doc_2.save(pdf_2_path)
    doc_2.close()
    print(f"[PDF Gen] Created {pdf_2_path}")


if __name__ == "__main__":
    generate_pdfs()
