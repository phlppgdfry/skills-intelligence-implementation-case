# Environments and security

## Environments

| Stage | Workday | SuccessFactors | Jira | Teams | Data |
|---|---|---|---|---|---|
| Build | implementation tenant (`norvane_impl`) | preview / test instance | a copy project (`ELEC-TEST`) | dev Teams tenant | synthetic (this repo) + a masked extract |
| UAT | sandbox refreshed from production in week 9 | test instance refreshed | production site, read-only | production Teams, pilot group only | production data, pilot population |
| Production | production tenant | production instance | production site | production Teams | production |

Three rules:

- Tenant names and URLs are **configuration, never code** (`TENANT` in `landscape.py` is the build default).
- No production data in the build environment. The readiness scan runs on the production extract **inside the customer's agreed processing location**, not on a laptop.
- A sandbox refresh wipes the integration's security configuration in some HCMs. Re-applying it is a step in the [cutover runbook](../05-delivery/cutover-and-hypercare.md).

## Accounts and least privilege

| Account | System | Can | Cannot |
|---|---|---|---|
| `ISU_SkillsLayer` | Workday | read workers, job profiles and the two custom reports; write skills on the worker profile | read compensation, personal data beyond the mapped fields, write anything else |
| `skillslayer_api` | SuccessFactors | read User, EmpJob, FOJobCode, cust_AboutMe | write; read compensation or other MDF objects |
| `svc-skillslayer` | Jira | browse the projects in scope | read service-desk projects, admin APIs |
| Teams bot app | Entra ID | send cards to users in the pilot group, receive their answers | read chats, channels or files |
| SFTP user | customer SFTP | read LMS/consent folders, write the Visier folder | anything else |

Workday security is granted through an integration system security group (ISSG) with domain permissions; the HRIS lead approves each domain in writing.

## Authentication

- **Workday:** OAuth 2.0 with an API client registered for the ISU. Refresh tokens are stored in the secret store and rotated as Workday's token policy requires.
- **SuccessFactors:** OAuth 2.0 SAML bearer assertion (company ID, client ID, signed assertion → token). Basic authentication for SuccessFactors APIs is being retired, so it is not an option even for the build.
- **Jira Cloud:** API token for the service account, Basic auth over HTTPS (Atlassian's documented pattern for scripts). Rotated every 90 days.
- **Teams:** an Entra ID app registration with admin consent. Bot Framework tokens are validated on every incoming activity.
- **SFTP:** key-based, one key per direction, the IP allowlisted.

## Secrets and network

- Secrets live in the platform's secret store (Azure Key Vault in Norvane's standard) and are never in config files or logs. The mock token in this repo is labelled `dev-token-not-a-secret`.
- Outbound calls only go to the documented hosts. The customer allowlists the platform's published egress IPs on the SFTP server and, where used, on the Workday tenant's IP restrictions.
- SSO for HR users of the platform goes through Norvane's Entra ID (SAML or OIDC). Access is managed by group; no local accounts.

## Logging and what not to log

The run log holds counts, IDs and statuses. It never holds free text, skill evidence sentences or emails. Evidence sentences stay in the platform and are shown only to the employee and, after validation, to HR roles that the works council agreement allows.

## Security review

Norvane's IT security questionnaire is answered from the vendor's standard pack (for example ISO/IEC 27001 and the vendor's DPA). This repository adds the customer-specific part: the accounts above, data flows, retention and the quarantine rule.
