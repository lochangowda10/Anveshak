# Security Policy — ANVESHAK

## 1. Scope & Sensitivity Notice

ANVESHAK processes **victim complaint records, wallet addresses, and law-enforcement investigative artifacts** for Smart India Hackathon 2026 (`SIH26183`, Team PHANTOMS).

> [!CAUTION]
> **MVP Seed Data Notice:** All VASP labels shipped in `docs/DATA_MODEL.md` (§7) and `backend/app/scripts/seed_labels.py` are **synthetic/placeholder TRON addresses** for development and hackathon testing. Never issue real legal notices (CrPC 91 / CrPC 102 / BNSS 94) solely on MVP placeholder attribution without independent verification.

---

## 2. Repository Hygiene Rules

- **Never commit secrets or `.env` files.** Only `.env.example` with placeholder values may be tracked in Git.
- **No hardcoded credentials or private keys:** Load `TRONGRID_API_KEY`, `DATABASE_URL`, and `SECRET_KEY` strictly via environment variables / `pydantic-settings`.
- **Victim PII protection:** Encrypt `cases.victim_contact` at the application layer in production deployments and restrict PostgreSQL and exported `backend/storage/action_packages/` volumes to authorized hosts.
- **SQL & Input Safety:** Use SQLAlchemy parameterized ORM queries exclusively and validate all TRON addresses (`^T[1-9A-HJ-NP-Za-km-z]{33}$`) and transaction hashes (`^[a-fA-F0-9]{64}$`) via Pydantic v2 schemas.

---

## 3. Reporting a Security Vulnerability

If you discover a security vulnerability, exposed secret, or unsafe data flow:

1. **Do NOT open a public GitHub issue** with exploit details or secret values.
2. Contact the Team Lead (**Lochan**) directly or open a private GitHub Security Advisory on the repository.
3. If a secret or API key was accidentally committed, **rotate/revoke the key immediately** before cleaning Git history.
