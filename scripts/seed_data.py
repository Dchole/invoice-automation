#!/usr/bin/env python3
"""Generate seed data: 100 clients, 240 sessions, invoices, and payments."""
import sys, os, random
from datetime import date, time, timedelta, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import engine, SessionLocal, Base
from app.models.client import Client
from app.models.session import Session
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.reminder import Reminder  # needed for relationship resolution

# --- Config ---
NUM_CLIENTS = 100
NUM_SESSIONS = 240
MONTHS_SPAN = 4  # sessions spread across Dec 2025 - Mar 2026
INVOICE_CUTOFF = 230  # first 230 sessions get invoices (last 10 don't)
PAYMENT_RATE = 0.90  # 90% of invoices are paid

PAYMENT_METHODS = ["e-transfer", "check", "cash", "stripe", "paypal"]

FIRST_NAMES = [
    "Alice", "Bob", "Carlos", "Diana", "Erik", "Fatima", "George", "Hannah",
    "Ivan", "Julia", "Kevin", "Laura", "Marco", "Nina", "Oscar", "Priya",
    "Quinn", "Rachel", "Sam", "Tanya", "Uma", "Victor", "Wendy", "Xander",
    "Yuki", "Zara", "Aaron", "Bella", "Chris", "Dina", "Ethan", "Fiona",
    "Grant", "Holly", "Ian", "Jade", "Kyle", "Lena", "Mike", "Nora",
    "Owen", "Paige", "Reed", "Sophie", "Tyler", "Ursula", "Vince", "Willa",
    "Xavier", "Yvonne"
]
LAST_NAMES = [
    "Anderson", "Baker", "Chen", "Diaz", "Evans", "Foster", "Garcia", "Hayes",
    "Ivanov", "Jensen", "Kim", "Li", "Martinez", "Nguyen", "O'Brien", "Patel",
    "Quinn", "Russo", "Silva", "Torres", "Ueda", "Valdez", "Walsh", "Xu",
    "Yamamoto", "Zhang", "Abbott", "Brooks", "Clarke", "Davis", "Ellis",
    "Fischer", "Green", "Hunt", "Jackson", "Knight", "Lee", "Moore", "Nash",
    "Palmer", "Reeves", "Stone", "Thomas", "Underwood", "Vargas", "White",
    "Young", "Zimmerman", "Black", "Cole"
]
COMPANIES = [
    "Maple Leaf Studios", "Northern Lights Design", "Pacific Web Co", "Summit Digital",
    "Horizon Analytics", "Blue Ridge Consulting", "Evergreen Labs", "Silver Creek Media",
    "Wildfire Creative", "Cascade Software", "Pinnacle Solutions", "Lakeside Tech",
    "Redwood Strategies", "Trailblaze Marketing", "Frostbite Games", "Coral Reef Apps",
    "Ironclad Security", "Velvet Sound Studio", "Amber Wave Films", "Starlight Events",
    None, None, None, None, None  # some clients have no company
]

SESSION_DESCRIPTIONS = [
    "Initial project kickoff and scope discussion",
    "UI wireframe review and feedback session",
    "Backend API architecture planning",
    "Database schema design workshop",
    "Sprint planning and task breakdown",
    "Code review and refactoring discussion",
    "Bug triage and prioritization meeting",
    "User testing debrief and action items",
    "Landing page design iteration",
    "Payment integration troubleshooting",
    "SEO audit and recommendations walkthrough",
    "Mobile responsive layout adjustments",
    "Brand guidelines review session",
    "Performance optimization deep-dive",
    "Client onboarding and setup walkthrough",
    "Content strategy brainstorm",
    "Analytics dashboard configuration",
    "Email template design review",
    "Security audit findings discussion",
    "Deployment pipeline setup and testing",
    "Third-party API integration planning",
    "Data migration strategy session",
    "Accessibility compliance review",
    "Social media campaign planning",
    "Quarterly progress review and roadmap update",
    "Invoice workflow automation demo",
    "CRM integration scoping call",
    "Video editing feedback and revisions",
    "Photography selection and layout review",
    "Contract renewal and scope expansion talk",
]

CLIENT_NOTES = [
    "Prefers morning meetings before 10 AM",
    "Key contact for all design approvals",
    "Usually pays within a week, very reliable",
    "Referred by a mutual contact at the tech meetup",
    "Needs detailed time breakdowns on invoices",
    "Prefers email over phone calls",
    "Long-term client, flexible on rates",
    "Startup — budget-conscious but growing fast",
    "Government contract, strict invoicing rules",
    "Always asks for PDF copies of invoices",
    "Responsive and easy to work with",
    "Tends to scope-creep, keep boundaries clear",
    "Pays promptly via e-transfer every time",
    "Multiple projects running in parallel",
    "Seasonal work — busier in Q1 and Q4",
    "Requires bilingual (EN/FR) deliverables",
    "Recently expanded team, more work coming",
    "Non-profit rate applies",
    "Timezone is PST — schedule accordingly",
    "Likes weekly status update emails",
]

INVOICE_NOTES = [
    "Includes all sessions for this billing period",
    "Rush project — premium rate applied",
    "Discounted rate per annual agreement",
    "Final invoice for phase one deliverables",
    "Covers additional revision rounds requested",
    "Travel expenses included in subtotal",
    "Split billing — second half of project",
    "Pro-rated for partial month engagement",
    "Retainer invoice — monthly fixed fee",
    "Overtime hours billed at 1.5x rate",
    "Early payment discount applied (2%)",
    "Adjusted for scope change mid-project",
    "Includes third-party software license cost",
    "Quarterly review and maintenance bundle",
    "Emergency support hours from last week",
]

PAYMENT_NOTES = [
    "Paid on time as usual",
    "Sent confirmation receipt via email",
    "Partial payment — remainder due next month",
    "Paid early, much appreciated",
    "Reference number noted for records",
    "Cleared after a short delay",
    "Payment received with thank-you note",
    "Auto-payment from recurring setup",
    "Paid in full, project complete",
    "Wire transfer confirmed by bank",
    "Check deposited, 3-day hold",
    "Stripe fee deducted from amount",
    "PayPal transaction ID logged",
    "Client paid from a different account",
    "Matched to invoice after manual review",
]

random.seed(42)


def random_date_in_range(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def main():
    # Recreate all tables (clears existing data)
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "invoices.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    Base.metadata.create_all(engine)

    db = SessionLocal()

    # --- Create 100 clients ---
    clients = []
    used_names = set()
    for i in range(NUM_CLIENTS):
        while True:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"
            if name not in used_names:
                used_names.add(name)
                break
        email_last = last.lower().replace("'", "")
        email = f"{first.lower()}.{email_last}@example.com"
        company = random.choice(COMPANIES)
        rate = random.choice([75, 85, 95, 100, 110, 120, 125, 135, 150])
        terms = random.choice([15, 30, 30, 30, 45])  # 30 is most common
        c = Client(
            name=name,
            email=email,
            company=company,
            currency="CAD",
            default_rate=rate,
            payment_terms=terms,
            notes=random.choice(CLIENT_NOTES),
        )
        db.add(c)
        clients.append(c)

    db.flush()  # assign IDs

    # --- Create 240 sessions spread across 4 months ---
    month_starts = [
        date(2025, 12, 1),
        date(2026, 1, 1),
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]
    month_ends = [
        date(2025, 12, 31),
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
    ]

    sessions = []
    for i in range(NUM_SESSIONS):
        month_idx = i % MONTHS_SPAN
        client = random.choice(clients)
        sess_date = random_date_in_range(month_starts[month_idx], month_ends[month_idx])
        duration = random.choice([30, 45, 60, 60, 90, 90, 120])
        rate = float(client.default_rate) if client.default_rate else 100.0
        amount = round(rate * duration / 60, 2)
        hour = random.randint(8, 16)
        minute = random.choice([0, 0, 15, 30, 45])
        start_t = time(hour, minute)
        end_minutes = hour * 60 + minute + duration
        end_t = time(min(end_minutes // 60, 23), end_minutes % 60)

        s = Session(
            client_id=client.id,
            date=sess_date,
            start_time=start_t,
            end_time=end_t,
            duration_minutes=duration,
            hourly_rate=rate,
            amount=amount,
            description=random.choice(SESSION_DESCRIPTIONS),
            status="unbilled",
        )
        db.add(s)
        sessions.append(s)

    db.flush()

    # --- Create invoices for first 230 sessions ---
    # Group billable sessions by client
    billable = sessions[:INVOICE_CUTOFF]
    client_sessions: dict[int, list[Session]] = {}
    for s in billable:
        client_sessions.setdefault(s.client_id, []).append(s)

    invoices = []
    inv_num = 1
    for client_id, sess_list in client_sessions.items():
        # Sort by date, create one invoice per batch of sessions
        sess_list.sort(key=lambda s: s.date)
        # Group into chunks of ~3-5 sessions per invoice
        chunk_size = random.randint(2, 5)
        for j in range(0, len(sess_list), chunk_size):
            chunk = sess_list[j : j + chunk_size]
            subtotal = sum(float(s.amount) for s in chunk)
            tax_rate = random.choice([0, 5, 13, 13, 15])  # GST/HST variations
            tax_amount = round(subtotal * tax_rate / 100, 2)
            total = round(subtotal + tax_amount, 2)
            issue = max(s.date for s in chunk) + timedelta(days=random.randint(1, 3))
            client = next(c for c in clients if c.id == client_id)
            due = issue + timedelta(days=client.payment_terms)

            inv = Invoice(
                invoice_number=f"INV-{inv_num:04d}",
                client_id=client_id,
                issue_date=issue,
                due_date=due,
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total=total,
                amount_paid=0,
                currency=client.currency,
                status="sent",
                sent_at=datetime.combine(issue, time(9, 0)),
                notes=random.choice(INVOICE_NOTES),
            )
            db.add(inv)
            db.flush()

            for s in chunk:
                s.status = "billed"
                s.invoice_id = inv.id

            invoices.append(inv)
            inv_num += 1

    db.flush()

    # --- Pay 90% of invoices ---
    payable = random.sample(invoices, k=int(len(invoices) * PAYMENT_RATE))
    for inv in payable:
        pay_date = inv.issue_date + timedelta(days=random.randint(2, inv.due_date.day if inv.due_date.day > 2 else 15))
        # clamp to reasonable range
        pay_date = min(pay_date, inv.due_date + timedelta(days=5))
        method = random.choice(PAYMENT_METHODS)
        ref_prefix = {"e-transfer": "ET", "check": "CHK", "cash": "CASH",
                       "stripe": "STR", "paypal": "PP"}
        ref = f"{ref_prefix[method]}-{random.randint(100000, 999999)}"

        p = Payment(
            invoice_id=inv.id,
            amount=float(inv.total),
            payment_date=pay_date,
            payment_method=method,
            reference=ref,
            notes=random.choice(PAYMENT_NOTES),
        )
        db.add(p)
        inv.amount_paid = float(inv.total)
        inv.status = "paid"
        inv.paid_at = datetime.combine(pay_date, time(14, 0))

    # Mark unpaid invoices as overdue if past due
    today = date(2026, 4, 19)
    for inv in invoices:
        if inv.status != "paid" and inv.due_date < today:
            inv.status = "overdue"

    db.commit()

    # --- Summary ---
    total_clients = db.query(Client).count()
    total_sessions = db.query(Session).count()
    total_invoices = db.query(Invoice).count()
    total_payments = db.query(Payment).count()
    paid_invoices = db.query(Invoice).filter(Invoice.status == "paid").count()

    print(f"Seed data created:")
    print(f"  Clients:  {total_clients}")
    print(f"  Sessions: {total_sessions}")
    print(f"  Invoices: {total_invoices} ({paid_invoices} paid, {total_invoices - paid_invoices} unpaid/overdue)")
    print(f"  Payments: {total_payments}")

    db.close()


if __name__ == "__main__":
    main()
