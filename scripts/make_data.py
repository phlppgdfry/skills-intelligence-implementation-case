"""Generate the synthetic Norvane Group landscape and its gold labels.

    python3 scripts/make_data.py           # write data/
    python3 scripts/make_data.py --check   # CI: fail if data/ is not what this script produces

Everything is seeded, so the same script always writes the same files. The
generator knows the truth (who is who, which skills a text really mentions,
which defects were planted) and writes it to data/gold/. The toolkit in
skillslayer/ never reads data/gold/; only evals/ do. That separation is what
makes the eval numbers mean something: the generator and the code under test
were written independently and only meet in the eval.

The data is invented. Names are combinations of common first and last names;
any resemblance to a real person is accidental. Domains use .example.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AS_OF = date(2026, 10, 1)
SEED = 20261021

# --------------------------------------------------------------------------- taxonomy
# (id, name, cluster, domain, neutral, aliases per language, context words if ambiguous, wild forms)
# neutral: the name is used as-is in every language (tool and technology names).
# context: an alias in this list is ambiguous and only counts with one of these words nearby.
# wild: surface forms people really write that are NOT in the taxonomy (typos, compounds).
#       Only the generator knows them; they are the realistic misses.
T = [
    ("SK-001", "High-voltage systems", "Electrical engineering", "Engineering", False,
     {"en": ["high voltage", "HV systems"], "nl": ["hoogspanning", "hoogspanningsinstallaties"], "de": ["Hochspannung", "Hochspannungstechnik"], "fr": ["haute tension"]}, None, ["Hochspannungsanlagenbau"]),
    ("SK-002", "Power electronics", "Electrical engineering", "Engineering", False,
     {"en": ["power electronics"], "nl": ["vermogenselektronica"], "de": ["Leistungselektronik"], "fr": ["électronique de puissance"]}, None, []),
    ("SK-003", "Battery systems", "Electrical engineering", "Engineering", False,
     {"en": ["battery systems", "battery packs", "BMS"], "nl": ["batterijsystemen"], "de": ["Batteriesysteme", "Batteriespeicher"], "fr": ["systèmes de batteries"]}, None, ["Batteriespeichertechnik"]),
    ("SK-004", "PLC programming", "Automation", "Engineering", False,
     {"en": ["PLC", "PLC programming", "Siemens TIA Portal"], "nl": ["PLC-programmatie", "PLC programmeren"], "de": ["SPS-Programmierung", "SPS"], "fr": ["programmation d'automates", "automates programmables"]}, None, ["S7 logic"]),
    ("SK-005", "SCADA", "Automation", "Engineering", True,
     {"en": ["SCADA", "WinCC"], "nl": [], "de": ["Prozessleittechnik"], "fr": ["supervision SCADA"]}, None, []),
    ("SK-006", "Electrical safety", "Electrical engineering", "Engineering", False,
     {"en": ["electrical safety", "NEN 3140", "lockout tagout"], "nl": ["elektrische veiligheid", "BA4", "BA5"], "de": ["Elektrosicherheit", "DGUV V3"], "fr": ["sécurité électrique", "habilitation électrique"]}, None, []),
    ("SK-007", "Motor control", "Electrical engineering", "Engineering", False,
     {"en": ["motor control", "variable frequency drives", "VFD"], "nl": ["motorsturing", "frequentieregelaars"], "de": ["Antriebstechnik", "Frequenzumrichter"], "fr": ["variateurs de fréquence"]}, None, []),
    ("SK-008", "EPLAN", "Electrical engineering", "Engineering", True,
     {"en": ["EPLAN Electric P8"], "nl": [], "de": [], "fr": []}, None, ["E-Plan"]),
    ("SK-009", "SolidWorks", "Mechanical engineering", "Engineering", True,
     {"en": ["Solidworks"], "nl": [], "de": [], "fr": []}, None, ["Solid Works"]),
    ("SK-010", "Finite element analysis", "Mechanical engineering", "Engineering", False,
     {"en": ["FEA", "finite element analysis", "ANSYS"], "nl": ["eindige-elementenanalyse"], "de": ["FEM-Analyse", "Finite-Elemente-Methode"], "fr": ["éléments finis"]}, None, ["FEM simulations"]),
    ("SK-011", "Hydraulics", "Mechanical engineering", "Engineering", False,
     {"en": ["hydraulics", "hydraulic systems"], "nl": ["hydrauliek"], "de": ["Hydraulik"], "fr": ["hydraulique"]}, None, []),
    ("SK-012", "Welding", "Mechanical engineering", "Engineering", False,
     {"en": ["welding", "TIG welding", "MIG welding"], "nl": ["lassen", "TIG-lassen"], "de": ["Schweißen", "WIG-Schweißen"], "fr": ["soudage"]}, None, ["Schweisstechnik"]),
    ("SK-013", "GD&T", "Mechanical engineering", "Engineering", True,
     {"en": ["geometric dimensioning and tolerancing"], "nl": ["vorm- en plaatstoleranties"], "de": ["Form- und Lagetolerierung"], "fr": ["cotation fonctionnelle"]}, None, []),
    ("SK-014", "Preventive maintenance", "Maintenance", "Engineering", False,
     {"en": ["preventive maintenance", "maintenance planning"], "nl": ["preventief onderhoud", "onderhoudsplanning"], "de": ["vorbeugende Instandhaltung", "Wartungsplanung"], "fr": ["maintenance préventive"]}, None, ["Instandhaltungsplanung"]),
    ("SK-015", "Python", "Software development", "Digital", True,
     {"en": ["Python 3", "pandas"], "nl": [], "de": [], "fr": []}, None, ["Pyhton"]),
    ("SK-016", "Java", "Software development", "Digital", True,
     {"en": ["Java 21"], "nl": [], "de": [], "fr": []}, None, []),
    ("SK-017", "Spring Boot", "Software development", "Digital", True,
     {"en": ["Spring"], "nl": [], "de": [], "fr": []}, ["java", "boot", "framework", "microservice", "rest"], []),
    ("SK-018", "SQL", "Data", "Digital", True,
     {"en": ["PostgreSQL", "T-SQL"], "nl": [], "de": [], "fr": []}, None, []),
    ("SK-019", "C++", "Software development", "Digital", True,
     {"en": ["modern C++"], "nl": [], "de": [], "fr": []}, None, ["cpp"]),
    ("SK-020", "Embedded C", "Software development", "Digital", True,
     {"en": ["embedded software", "firmware"], "nl": ["embedded software"], "de": ["Embedded-Software", "Firmware"], "fr": ["logiciel embarqué"]}, None, []),
    ("SK-021", "Git", "Software development", "Digital", True,
     {"en": ["GitLab", "GitHub"], "nl": [], "de": [], "fr": []}, None, []),
    ("SK-022", "CI/CD", "DevOps", "Digital", True,
     {"en": ["continuous integration", "build pipelines"], "nl": ["build-pipelines"], "de": ["Build-Pipelines"], "fr": ["intégration continue"]}, None, []),
    ("SK-023", "Docker", "DevOps", "Digital", True,
     {"en": ["containers"], "nl": ["containers"], "de": ["Container"], "fr": ["conteneurs"]}, None, []),
    ("SK-024", "Kubernetes", "DevOps", "Digital", True,
     {"en": ["k8s", "AKS"], "nl": [], "de": [], "fr": []}, None, ["kube"]),
    ("SK-025", "REST APIs", "Software development", "Digital", True,
     {"en": ["REST API", "OpenAPI"], "nl": [], "de": ["REST-Schnittstellen"], "fr": []}, None, []),
    ("SK-026", "Microsoft Azure", "Cloud", "Digital", True,
     {"en": ["Azure"], "nl": [], "de": [], "fr": []}, None, []),
    ("SK-027", "Data pipelines", "Data", "Digital", False,
     {"en": ["data pipelines", "ETL"], "nl": ["datapipelines"], "de": ["Datenpipelines", "ETL-Strecken"], "fr": ["pipelines de données"]}, None, []),
    ("SK-028", "Machine learning", "Data", "Digital", False,
     {"en": ["machine learning", "ML models"], "nl": [], "de": ["maschinelles Lernen"], "fr": ["apprentissage automatique"]}, None, []),
    ("SK-029", "Power BI", "Data", "Digital", True,
     {"en": ["DAX"], "nl": [], "de": [], "fr": []}, None, ["PowerBI"]),
    ("SK-030", "Microsoft Excel", "Office", "Business", True,
     {"en": ["Excel"], "nl": [], "de": [], "fr": []}, ["spreadsheet", "pivot", "macro", "vba", "formulas", "rekenblad", "tabellen", "tableur", "sheet"], []),
    ("SK-031", "ISO 9001", "Quality", "Operations", True,
     {"en": ["quality management system"], "nl": ["kwaliteitszorgsysteem"], "de": ["Qualitätsmanagementsystem"], "fr": ["système de management de la qualité"]}, None, []),
    ("SK-032", "Root cause analysis", "Quality", "Operations", False,
     {"en": ["root cause analysis", "8D", "5 whys"], "nl": ["oorzakenanalyse"], "de": ["Ursachenanalyse", "8D-Report"], "fr": ["analyse des causes"]}, None, []),
    ("SK-033", "FMEA", "Quality", "Operations", True,
     {"en": ["failure mode and effects analysis"], "nl": [], "de": [], "fr": ["AMDEC"]}, None, []),
    ("SK-034", "Lean manufacturing", "Continuous improvement", "Operations", False,
     {"en": ["lean manufacturing", "lean", "kaizen"], "nl": ["lean", "lean productie"], "de": ["Lean Production", "Lean"], "fr": ["lean manufacturing", "lean"]}, ["manufacturing", "production", "kaizen", "5s", "productie", "produktion", "verspilling", "waste", "gaspillage"], []),
    ("SK-035", "Statistical process control", "Quality", "Operations", False,
     {"en": ["SPC", "statistical process control"], "nl": ["statistische procescontrole"], "de": ["statistische Prozessregelung"], "fr": ["maîtrise statistique des procédés"]}, None, []),
    ("SK-036", "Supply chain planning", "Supply chain", "Operations", False,
     {"en": ["supply chain planning", "S&OP", "demand planning"], "nl": ["supply chain planning", "vraagplanning"], "de": ["Supply-Chain-Planung", "Bedarfsplanung"], "fr": ["planification de la chaîne logistique"]}, None, []),
    ("SK-037", "Procurement", "Supply chain", "Operations", False,
     {"en": ["procurement", "purchasing", "sourcing"], "nl": ["aankoop", "inkoop"], "de": ["Einkauf", "Beschaffung"], "fr": ["achats"]}, None, []),
    ("SK-038", "SAP MM", "ERP", "Operations", True,
     {"en": ["SAP Materials Management"], "nl": [], "de": [], "fr": []}, None, []),
    ("SK-039", "Inventory management", "Supply chain", "Operations", False,
     {"en": ["inventory management", "stock control"], "nl": ["voorraadbeheer"], "de": ["Bestandsmanagement", "Lagerverwaltung"], "fr": ["gestion des stocks"]}, None, []),
    ("SK-040", "Production scheduling", "Supply chain", "Operations", False,
     {"en": ["production scheduling", "production planning"], "nl": ["productieplanning"], "de": ["Produktionsplanung", "Fertigungssteuerung"], "fr": ["ordonnancement"]}, None, []),
    ("SK-041", "Health and safety", "Safety", "Operations", False,
     {"en": ["health and safety", "HSE", "risk assessment"], "nl": ["veiligheid en welzijn", "VCA"], "de": ["Arbeitssicherheit", "Gefährdungsbeurteilung"], "fr": ["santé et sécurité", "prévention"]}, None, []),
    ("SK-042", "Forklift operation", "Logistics", "Operations", False,
     {"en": ["forklift", "reach truck"], "nl": ["heftruck", "reachtruck"], "de": ["Gabelstapler", "Staplerschein"], "fr": ["chariot élévateur", "cariste"]}, None, []),
    ("SK-043", "Project management", "Management", "Business", False,
     {"en": ["project management", "PMP", "PRINCE2"], "nl": ["projectmanagement", "projectbeheer"], "de": ["Projektmanagement", "Projektleitung"], "fr": ["gestion de projet"]}, None, ["Projektmanagementerfahrung"]),
    ("SK-044", "Stakeholder management", "Management", "Business", False,
     {"en": ["stakeholder management"], "nl": ["stakeholdermanagement"], "de": ["Stakeholder-Management"], "fr": ["gestion des parties prenantes"]}, None, []),
    ("SK-045", "Contract negotiation", "Commercial", "Business", False,
     {"en": ["contract negotiation", "negotiation"], "nl": ["contractonderhandeling", "onderhandelen"], "de": ["Vertragsverhandlung", "Verhandlungsführung"], "fr": ["négociation"]}, None, []),
    ("SK-046", "Budgeting", "Finance", "Business", False,
     {"en": ["budgeting", "budget control"], "nl": ["budgetbeheer", "budgettering"], "de": ["Budgetierung", "Budgetverantwortung"], "fr": ["gestion budgétaire"]}, None, []),
    ("SK-047", "Financial reporting", "Finance", "Business", False,
     {"en": ["financial reporting", "month-end closing"], "nl": ["financiële rapportering", "maandafsluiting"], "de": ["Finanzberichterstattung", "Monatsabschluss"], "fr": ["reporting financier", "clôture mensuelle"]}, None, []),
    ("SK-048", "IFRS", "Finance", "Business", True,
     {"en": ["International Financial Reporting Standards"], "nl": [], "de": [], "fr": []}, None, []),
    ("SK-049", "People management", "Leadership", "Business", False,
     {"en": ["people management", "team leadership", "line management"], "nl": ["people management", "leidinggeven", "teamleiding"], "de": ["Personalführung", "Mitarbeiterführung"], "fr": ["management d'équipe", "encadrement"]}, None, []),
    ("SK-050", "Coaching", "Leadership", "Business", False,
     {"en": ["coaching", "mentoring"], "nl": ["coaching", "coachen"], "de": ["Coaching"], "fr": ["coaching", "accompagnement"]}, None, []),
    ("SK-051", "Change management", "Management", "Business", False,
     {"en": ["change management", "ADKAR"], "nl": ["verandermanagement"], "de": ["Veränderungsmanagement", "Change-Management"], "fr": ["conduite du changement"]}, None, []),
    ("SK-052", "Customer service", "Commercial", "Business", False,
     {"en": ["customer service", "customer support"], "nl": ["klantenservice", "klantendienst"], "de": ["Kundenservice", "Kundenbetreuung"], "fr": ["service client"]}, None, []),
    ("SK-053", "Technical sales", "Commercial", "Business", False,
     {"en": ["technical sales", "pre-sales"], "nl": ["technische verkoop"], "de": ["technischer Vertrieb"], "fr": ["vente technique", "avant-vente"]}, None, []),
    ("SK-054", "Technical writing", "Communication", "Business", False,
     {"en": ["technical writing", "technical documentation"], "nl": ["technische documentatie"], "de": ["technische Dokumentation", "technische Redaktion"], "fr": ["rédaction technique"]}, None, []),
    ("SK-055", "Data analysis", "Data", "Digital", False,
     {"en": ["data analysis", "analytics"], "nl": ["data-analyse"], "de": ["Datenanalyse"], "fr": ["analyse de données"]}, None, []),
    ("SK-056", "Cybersecurity", "Cloud", "Digital", False,
     {"en": ["cybersecurity", "IEC 62443", "network security"], "nl": ["cyberbeveiliging"], "de": ["IT-Sicherheit", "Cybersicherheit"], "fr": ["cybersécurité"]}, None, []),
    ("SK-057", "Robotics", "Automation", "Engineering", False,
     {"en": ["robotics", "industrial robots", "cobots"], "nl": ["robotica"], "de": ["Robotik", "Industrieroboter"], "fr": ["robotique"]}, None, []),
    ("SK-058", "Charging infrastructure", "Electrical engineering", "Engineering", False,
     {"en": ["charging infrastructure", "EV charging", "OCPP"], "nl": ["laadinfrastructuur", "laadpalen"], "de": ["Ladeinfrastruktur", "Ladesäulen"], "fr": ["infrastructure de recharge", "bornes de recharge"]}, None, ["Ladeinfrastrukturprojekte"]),
]

LANGS = ("en", "nl", "de", "fr")

# Names for the two companies. Combinations are generated; duplicates are avoided
# except for the homonyms that are planted on purpose.
NV_FIRST = ["Lotte", "Wout", "Emma", "Jonas", "Lies", "Pieter", "Sara", "Ruben", "Anouk", "Tom", "Eline", "Bram",
            "Nina", "Arne", "Marie", "Koen", "Hanne", "Stijn", "Femke", "Joris", "Inès", "Mehdi", "Yasmine", "Karim",
            "Chloé", "Lucas", "Amélie", "Thibault", "Fatima", "Olivier"]
NV_LAST = ["Peeters", "Janssens", "Maes", "Jacobs", "Mertens", "Willems", "Claes", "Goossens", "Wouters", "De Smet",
           "Dubois", "Lambert", "Hermans", "Aerts", "Vermeulen", "Van Damme", "Pauwels", "Martens", "Desmet", "El Amrani",
           "Leroy", "Michiels", "Coppens", "De Vos", "Verbeke", "Bogaert", "Laurent", "Renard", "Smets", "Cools"]
KD_FIRST = ["Jürgen", "Anna", "Lukas", "Sophie", "Felix", "Lena", "Jonas", "Marie", "Tobias", "Laura", "Stefan", "Julia",
            "Michael", "Katrin", "Sebastian", "Hannah", "Thomas", "Miriam", "Florian", "Sabine", "Björn", "Özlem", "Matthias", "Jana"]
KD_LAST = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
           "Koch", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger",
           "Hartmann", "Lange", "Weiß", "Groß"]

# Job architecture: (key, title_en, cluster focus skills, company)
ROLES = [
    ("electrical-engineer", "Electrical Engineer", ["SK-001", "SK-002", "SK-006", "SK-007", "SK-008", "SK-058"]),
    ("battery-engineer", "Battery Systems Engineer", ["SK-003", "SK-002", "SK-001", "SK-010", "SK-020"]),
    ("automation-engineer", "Automation Engineer", ["SK-004", "SK-005", "SK-007", "SK-057", "SK-056"]),
    ("mechanical-engineer", "Mechanical Design Engineer", ["SK-009", "SK-010", "SK-013", "SK-011"]),
    ("maintenance-technician", "Maintenance Technician", ["SK-014", "SK-011", "SK-006", "SK-012", "SK-041"]),
    ("welder", "Welder", ["SK-012", "SK-013", "SK-041"]),
    ("software-engineer", "Software Engineer", ["SK-016", "SK-017", "SK-018", "SK-021", "SK-025", "SK-022"]),
    ("embedded-engineer", "Embedded Software Engineer", ["SK-020", "SK-019", "SK-021", "SK-003"]),
    ("platform-engineer", "Platform Engineer", ["SK-023", "SK-024", "SK-022", "SK-026", "SK-056"]),
    ("data-engineer", "Data Engineer", ["SK-015", "SK-018", "SK-027", "SK-026", "SK-029"]),
    ("data-scientist", "Data Scientist", ["SK-015", "SK-028", "SK-055", "SK-018"]),
    ("quality-engineer", "Quality Engineer", ["SK-031", "SK-032", "SK-033", "SK-035"]),
    ("process-engineer", "Process Engineer", ["SK-034", "SK-035", "SK-032", "SK-040"]),
    ("supply-planner", "Supply Chain Planner", ["SK-036", "SK-039", "SK-038", "SK-030"]),
    ("buyer", "Buyer", ["SK-037", "SK-045", "SK-038", "SK-030"]),
    ("warehouse-operator", "Warehouse Operator", ["SK-042", "SK-039", "SK-041"]),
    ("project-manager", "Project Manager", ["SK-043", "SK-044", "SK-046", "SK-051"]),
    ("team-lead-production", "Production Team Lead", ["SK-049", "SK-050", "SK-040", "SK-041", "SK-034"]),
    ("controller", "Financial Controller", ["SK-047", "SK-048", "SK-046", "SK-030"]),
    ("sales-engineer", "Sales Engineer", ["SK-053", "SK-045", "SK-044", "SK-052"]),
    ("service-agent", "Customer Service Agent", ["SK-052", "SK-030"]),
    ("hr-business-partner", "HR Business Partner", ["SK-049", "SK-050", "SK-051", "SK-044"]),
    ("technical-writer", "Technical Writer", ["SK-054", "SK-021"]),
    ("security-engineer", "OT Security Engineer", ["SK-056", "SK-005", "SK-025"]),
]
TITLE_NL = {"Electrical Engineer": "Elektrotechnisch ingenieur", "Maintenance Technician": "Onderhoudstechnicus",
            "Welder": "Lasser", "Warehouse Operator": "Magazijnier", "Production Team Lead": "Ploegleider productie",
            "Buyer": "Aankoper", "Customer Service Agent": "Medewerker klantendienst"}
TITLE_DE = {"Electrical Engineer": "Elektroingenieur", "Battery Systems Engineer": "Ingenieur Batteriesysteme",
            "Automation Engineer": "Automatisierungsingenieur", "Mechanical Design Engineer": "Konstrukteur Maschinenbau",
            "Maintenance Technician": "Instandhaltungstechniker", "Welder": "Schweißer",
            "Embedded Software Engineer": "Embedded-Softwareentwickler", "Quality Engineer": "Qualitätsingenieur",
            "Supply Chain Planner": "Disponent", "Buyer": "Einkäufer", "Production Team Lead": "Schichtleiter Produktion",
            "Project Manager": "Projektleiter", "Sales Engineer": "Vertriebsingenieur"}

# --------------------------------------------------------------------------- sentence templates
SKILL_SENT = {
    "en": ["You have hands-on experience with {x}.", "Strong knowledge of {x} is required.", "You will work daily with {x}.", "Experience in {x} is a plus."],
    "nl": ["Je hebt praktische ervaring met {x}.", "Kennis van {x} is vereist.", "Je werkt dagelijks met {x}.", "Ervaring met {x} is een plus."],
    "de": ["Sie haben praktische Erfahrung mit {x}.", "Fundierte Kenntnisse in {x} sind erforderlich.", "Sie arbeiten täglich mit {x}.", "Erfahrung mit {x} ist von Vorteil."],
    "fr": ["Vous avez une expérience pratique en {x}.", "Une bonne connaissance de {x} est requise.", "Vous travaillez au quotidien avec {x}.", "Une expérience en {x} est un atout."],
}
NEG_GUARDED = {"en": "No experience with {x} is needed.", "nl": "Geen ervaring met {x} nodig.", "de": "Keine Erfahrung mit {x} erforderlich.", "fr": "Pas d'expérience en {x} requise."}
NEG_TRAILING = {"en": "{x} is not part of this role.", "nl": "{x} hoort niet bij deze functie.", "de": "{x} gehört nicht zu dieser Rolle.", "fr": "{x} ne fait pas partie de ce poste."}
ASPIRATION = {"en": "I would like to learn {x}.", "nl": "Ik wil graag {x} leren.", "de": "Ich möchte {x} lernen.", "fr": "J'aimerais apprendre {x}."}
AMBIGUOUS_SENT = {
    "en": ["You excel at keeping deadlines under pressure.", "The move to the new hall is planned for spring 2027.", "We keep the support team lean."],
    "nl": ["De verhuis naar de nieuwe hal staat gepland voor de lente; het Spring-congres in Gent is een extra.", "We houden het team bewust lean."],
    "de": ["Das Team ist schlank aufgestellt und bleibt lean.", "Der Umzug ist für das Frühjahr geplant; das Spring-Fest am Standort ist freiwillig."],
    "fr": ["Notre équipe reste lean et réactive.", "Le déménagement est prévu au printemps; le Spring Day est facultatif."],
}
FILLER = {
    "en": ["You join a team of {n} colleagues at the {site} site.", "Norvane builds electrification equipment for industry.", "You report to the department head."],
    "nl": ["Je komt terecht in een team van {n} collega's op de site in {site}.", "Norvane bouwt elektrificatie-installaties voor de industrie."],
    "de": ["Sie arbeiten in einem Team von {n} Kolleginnen und Kollegen am Standort {site}.", "Keldorf ist Teil der Norvane Group."],
    "fr": ["Vous rejoignez une équipe de {n} collègues sur le site de {site}.", "Norvane conçoit des équipements d'électrification."],
}
SITES = {"en": ["Antwerp", "Genk", "Wavre"], "nl": ["Antwerpen", "Genk"], "de": ["Dortmund", "Kassel"], "fr": ["Wavre", "Charleroi"]}
TICKET = {
    "en": ["Fix {x} timeout on line {n}", "Upgrade {x} on test bench {n}", "Investigate {x} alarm in hall {n}", "Document {x} procedure for the night shift", "Review {x} change for release {n}"],
    "nl": ["{x} storing oplossen op lijn {n}", "Procedure {x} documenteren voor ploeg {n}"],
    "de": ["{x}-Fehler an Linie {n} beheben", "{x} auf Prüfstand {n} aktualisieren"],
}
COURSE = {
    "en": ["Introduction to {x}", "{x} for practitioners", "Advanced {x}"],
    "nl": ["{x} voor beginners", "Opleiding {x}"],
    "de": ["{x} für Fortgeschrittene", "Grundlagen {x}"],
    "fr": ["Initiation à {x}", "Formation {x}"],
}
ABOUT_SKILL = {
    "de": ["Ich arbeite seit {n} Jahren mit {x}.", "In meinem letzten Projekt habe ich {x} eingesetzt."],
    "en": ["I have worked with {x} for {n} years.", "In my last project I used {x} every day."],
}
SENSITIVE = [  # planted: sensitive personal data in a free-text field
    ("health", "Nach meinem Burn-out im Jahr 2024 arbeite ich in Teilzeit."),
    ("union", "Ich bin Betriebsrat und Mitglied der IG Metall."),
    ("national_id", "Meine Steuer-ID für die Abrechnung: 12 345 678 901."),
    ("health", "After my back surgery I avoid heavy lifting."),
]


class Gen:
    def __init__(self) -> None:
        self.r = random.Random(SEED)
        self.skills = {t[0]: t for t in T}
        self.texts: dict[str, dict] = {}     # gold: text id -> {lang, skills, kind}
        self.defects: list[dict] = []        # gold: planted readiness defects

    # ------------------------------------------------------------ surface forms
    def surface(self, sid: str, lang: str, allow_wild: bool = True) -> tuple[str, bool]:
        """Return (form, is_wild). Wild forms are never in the taxonomy."""
        _, name, _, _, neutral, aliases, context, wild = self.skills[sid]
        if allow_wild and wild and self.r.random() < 0.18:
            return self.r.choice(wild), True
        forms = list(aliases.get(lang, []))
        if neutral or not forms:
            forms.append(name)
        if context:  # ambiguous alias: the generator only uses it when a context word follows
            forms = [f for f in forms if f not in aliases.get(lang, [])] or [name]
        return self.r.choice(forms), False

    def other_skill(self, exclude: set[str]) -> str:
        pool = [s for s in self.skills if s not in exclude and not self.skills[s][6]]
        return self.r.choice(pool)

    # ------------------------------------------------------------ text builders
    def job_text(self, tid: str, lang: str, skills: list[str], distractors: int) -> str:
        sents: list[str] = [self.r.choice(FILLER[lang]).format(n=self.r.randint(4, 25), site=self.r.choice(SITES[lang]))]
        gold = set()
        for sid in skills:
            form, _ = self.surface(sid, lang)
            sents.append(self.r.choice(SKILL_SENT[lang]).format(x=form))
            gold.add(sid)
        exclude = set(skills)
        for _ in range(distractors):
            kind = self.r.choice(["neg", "neg", "trailing", "ambiguous"])
            if kind == "ambiguous":
                sents.append(self.r.choice(AMBIGUOUS_SENT[lang]))
                continue
            y = self.other_skill(exclude)
            exclude.add(y)
            form, _ = self.surface(y, lang, allow_wild=False)
            sents.append((NEG_GUARDED if kind == "neg" else NEG_TRAILING)[lang].format(x=form))
        self.r.shuffle(sents)
        sents = [x[0].upper() + x[1:] for x in sents]
        self.texts[tid] = {"lang": lang, "kind": "job", "skills": sorted(gold)}
        return " ".join(sents)

    def ticket_text(self, tid: str, lang: str, sid: str) -> str:
        form, _ = self.surface(sid, lang)
        text = self.r.choice(TICKET[lang]).format(x=form, n=self.r.randint(1, 9))
        self.texts[tid] = {"lang": lang, "kind": "ticket", "skills": [sid]}
        return text

    def course_text(self, tid: str, lang: str, sid: str) -> str:
        form, _ = self.surface(sid, lang, allow_wild=False)
        text = self.r.choice(COURSE[lang]).format(x=form)
        self.texts[tid] = {"lang": lang, "kind": "course", "skills": [sid]}
        return text

    def about_text(self, tid: str, lang: str, skills: list[str], aspire: str | None, sensitive: str | None) -> str:
        sents = []
        for sid in skills:
            form, _ = self.surface(sid, lang)
            sents.append(self.r.choice(ABOUT_SKILL[lang]).format(x=form, n=self.r.randint(2, 15)))
        if aspire:
            form, _ = self.surface(aspire, lang, allow_wild=False)
            sents.append(ASPIRATION[lang].format(x=form))
        if sensitive:
            sents.append(sensitive)
        self.texts[tid] = {"lang": lang, "kind": "about", "skills": sorted(skills)}
        return " ".join(sents)


def ms_date(d: date) -> str:
    """SuccessFactors OData v2 date literal."""
    epoch = date(1970, 1, 1)
    return f"/Date({(d - epoch).days * 86_400_000})/"


def build() -> dict[str, str]:
    g = Gen()
    r = g.r
    out: dict[str, object] = {}

    # ----------------------------------------------------------- taxonomy (what the engine knows)
    out["taxonomy.json"] = {
        "version": "2026.3",
        "skills": [
            {"id": sid, "name": name, "cluster": cluster, "domain": domain,
             "aliases": {lang: list(a) for lang, a in aliases.items() if a},
             **({"context": context} if context else {})}
            for sid, name, cluster, domain, neutral, aliases, context, wild in T
        ],
    }

    # ----------------------------------------------------------- job architecture
    wd_jobs, sf_jobs = [], []
    role_skills: dict[str, list[str]] = {}
    job_of_role: dict[tuple[str, str], str] = {}
    for i, (key, title, skills) in enumerate(ROLES):
        role_skills[key] = skills
        # Norvane (Workday): every role, descriptions EN or NL
        jid = f"JP-{100 + i}"
        lang = "nl" if title in TITLE_NL and r.random() < 0.8 else "en"
        job_title = TITLE_NL.get(title, title) if lang == "nl" else title
        wd_jobs.append({"jid": jid, "title": job_title, "lang": lang, "skills": skills, "role": key})
        job_of_role[("wd", key)] = jid
        # Keldorf (SuccessFactors): engineering and operations roles, descriptions DE or EN
        if i % 4 != 3:
            code = f"KD-{2000 + i * 7}"
            lang = "de" if r.random() < 0.7 else "en"
            job_title = TITLE_DE.get(title, title) if lang == "de" else title
            sf_jobs.append({"jid": code, "title": job_title, "lang": lang, "skills": skills, "role": key})
            job_of_role[("sf", key)] = code
    # Wavre site uses French job descriptions for four roles
    for key in ("maintenance-technician", "warehouse-operator", "service-agent", "quality-engineer"):
        jid = f"JP-{200 + len(wd_jobs)}"
        title = dict((k, t) for k, t, _ in ROLES)[key]
        wd_jobs.append({"jid": jid, "title": f"{title} (Wavre)", "lang": "fr", "skills": role_skills[key], "role": key})
        job_of_role[("wd-fr", key)] = jid

    report_entries = []
    stale_jobs, short_jobs, dup_jobs = [], [], []
    for n, j in enumerate(wd_jobs):
        k = len(j["skills"])
        sk = r.sample(j["skills"], k=max(2, k - r.randint(0, 1)))
        text = g.job_text(j["jid"], j["lang"], sk, distractors=r.randint(1, 3))
        updated = AS_OF - timedelta(days=r.randint(30, 900))
        if n % 9 == 4:
            updated = AS_OF - timedelta(days=r.randint(1300, 2400))
            stale_jobs.append(j["jid"])
        if n % 11 == 7:  # planted: description missing
            text = ""
            g.texts[j["jid"]]["skills"] = []
            short_jobs.append(j["jid"])
        report_entries.append({
            "Job_Profile_ID": j["jid"], "Job_Profile_Name": j["title"], "Job_Family": j["role"].split("-")[0].title(),
            "Job_Description": text, "Language": j["lang"], "Last_Updated": updated.isoformat(), "Inactive": "0",
        })
    # planted: the same job twice under two codes (legacy import), one with zero incumbents
    for src_id, dup_id in (("JP-106", "JP-906"), ("JP-116", "JP-916")):
        src = next(e for e in report_entries if e["Job_Profile_ID"] == src_id)
        report_entries.append({**src, "Job_Profile_ID": dup_id, "Last_Updated": (AS_OF - timedelta(days=1500)).isoformat()})
        g.texts[dup_id] = {**g.texts[src_id]}
        dup_jobs.append({"jobs": [src_id, dup_id], "title": src["Job_Profile_Name"]})
    for jid in stale_jobs:
        g.defects.append({"check": "job_description_stale", "object": jid})
    for jid in short_jobs:
        g.defects.append({"check": "job_description_missing", "object": jid})
    for d in dup_jobs:
        g.defects.append({"check": "duplicate_job_title", "object": "|".join(sorted(d["jobs"]))})
        g.defects.append({"check": "job_without_incumbents", "object": d["jobs"][1]})
        g.defects.append({"check": "job_description_stale", "object": d["jobs"][1]})

    sf_jobcodes = []
    for j in sf_jobs:
        sk = r.sample(j["skills"], k=max(2, len(j["skills"]) - r.randint(0, 1)))
        text = g.job_text(j["jid"], j["lang"], sk, distractors=r.randint(1, 3))
        sf_jobcodes.append({
            "externalCode": j["jid"], "name": j["title"], "description": text, "language": j["lang"],
            "lastModifiedDateTime": ms_date(AS_OF - timedelta(days=r.randint(20, 700))), "status": "A",
        })

    # ----------------------------------------------------------- people
    used: set[str] = set()

    def name(firsts: list[str], lasts: list[str]) -> tuple[str, str]:
        while True:
            f, l = r.choice(firsts), r.choice(lasts)
            if (f, l) not in used:
                used.add((f, l))
                return f, l

    def email(first: str, last: str, domain: str) -> str:
        t = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "é": "e", "è": "e", "ï": "i", "ç": "c", "ë": "e", "Ö": "Oe", "Ü": "Ue", "Ä": "Ae"}
        norm = "".join(t.get(c, c) for c in f"{first}.{last}").lower().replace(" ", "")
        return f"{norm}@{domain}"

    persons = []  # the truth: one entry per real human
    nv_roles = [k for k, _, _ in ROLES]
    kd_roles = [j["role"] for j in sf_jobs]
    for i in range(170):
        f, l = name(NV_FIRST, NV_LAST)
        key = r.choice(nv_roles)
        jid = job_of_role[("wd", key)]
        country = "BE"
        if key in ("maintenance-technician", "warehouse-operator", "service-agent", "quality-engineer") and r.random() < 0.35:
            jid, country = job_of_role[("wd-fr", key)], "BE"
        persons.append({"pid": f"P{i + 1:04d}", "first": f, "last": l, "company": "norvane", "role": key, "job": jid, "country": country})
    for i in range(95):
        f, l = name(KD_FIRST, KD_LAST)
        key = r.choice(kd_roles)
        persons.append({"pid": f"P{i + 171:04d}", "first": f, "last": l, "company": "keldorf", "role": key, "job": job_of_role[("sf", key)], "country": "DE"})
    # planted homonym: a second, different Thomas Becker in Norvane (naive name matching merges them)
    hom = next(p for p in persons if p["company"] == "keldorf")
    persons.append({"pid": "P0266", "first": hom["first"], "last": hom["last"], "company": "norvane", "role": "project-manager",
                    "job": job_of_role[("wd", "project-manager")], "country": "BE"})

    # true skills per person
    all_ids = list(g.skills)
    for p in persons:
        rs = role_skills[p["role"]]
        true = {s for s in rs if r.random() < 0.7}
        extras = r.sample([s for s in all_ids if s not in rs], k=r.randint(1, 3))
        p["true"] = sorted(true | set(extras))
        p["hire"] = (date(2008, 1, 1) + timedelta(days=r.randint(0, 6500))).isoformat()

    # transferred Keldorf people: also hired into Workday after the merger (dual records)
    keldorf = [p for p in persons if p["company"] == "keldorf" and p["pid"] != hom["pid"]]
    transferred = r.sample(keldorf, k=26)
    for n, p in enumerate(transferred):
        p["transferred"] = True
        p["xref"] = n < 11                      # only some got the legacy id filled in Workday
        p["umlaut_variant"] = any(c in p["first"] + p["last"] for c in "äöüß") and n % 2 == 0
        p["sf_email_old"] = n % 3 != 0          # old @keldorf.example address still in SF

    # opt-outs (consent tool export)
    optouts = sorted(r.sample([p["pid"] for p in persons], k=7))

    # ----------------------------------------------------------- Workday workers (REST, paged) + current skills
    wd_workers, wd_skills_current, sf_users, sf_empjob, sf_profiles = [], [], [], [], []
    gold_identity: dict[str, str] = {}
    wd_id_of: dict[str, str] = {}
    sf_id_of: dict[str, str] = {}
    n_wd = 0

    def to_ascii(s: str) -> str:
        return s.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")

    for p in persons:
        if p["company"] == "norvane" or p.get("transferred"):
            n_wd += 1
            wid = f"W{30000 + n_wd * 3}"
            wd_id_of[p["pid"]] = wid
            first, last = (to_ascii(p["first"]), to_ascii(p["last"])) if p.get("umlaut_variant") else (p["first"], p["last"])
            job = p["job"]
            if p.get("transferred"):
                job = job_of_role.get(("wd", p["role"]), job)
            wd_workers.append({
                "id": wid, "descriptor": f"{first} {last}", "firstName": first, "lastName": last,
                "primaryWorkEmail": email(p["first"], p["last"], "norvane.example"),
                "jobProfile": {"id": job}, "location": p["country"],
                "hireDate": (AS_OF - timedelta(days=r.randint(60, 500))).isoformat() if p.get("transferred") else p["hire"],
                "manager": None, "legacySuccessFactorsId": None, "lastUpdated": (AS_OF - timedelta(days=r.randint(5, 400))).isoformat(),
            })
            gold_identity[f"workday:{wid}"] = p["pid"]
        if p["company"] == "keldorf":
            uid = f"kd{p['last'][:3].lower()}{p['first'][:2].lower()}{len(sf_users) + 10}"
            uid = to_ascii(uid)
            sf_id_of[p["pid"]] = uid
            dom = "keldorf.example" if p.get("sf_email_old", True) or not p.get("transferred") else "norvane.example"
            sf_users.append({"userId": uid, "firstName": p["first"], "lastName": p["last"], "email": email(p["first"], p["last"], dom),
                             "hireDate": ms_date(date.fromisoformat(p["hire"])), "status": "inactive" if p.get("transferred") and r.random() < 0.5 else "active",
                             "country": "DEU", "lastModifiedDateTime": ms_date(AS_OF - timedelta(days=r.randint(3, 300)))})
            gold_identity[f"successfactors:{uid}"] = p["pid"]
            # effective-dated job history: an old record and the current one
            old_start = date.fromisoformat(p["hire"])
            change = old_start + timedelta(days=r.randint(200, 1500))
            other = r.choice(sf_jobs)["jid"]
            sf_empjob += [
                {"userId": uid, "seqNumber": 1, "startDate": ms_date(old_start), "endDate": ms_date(change - timedelta(days=1)), "jobCode": other},
                {"userId": uid, "seqNumber": 2, "startDate": ms_date(change), "endDate": ms_date(date(9999, 12, 31)), "jobCode": p["job"]},
            ]
    # legacy cross-reference for some transferred people; manager links
    by_wid = {w["id"]: w for w in wd_workers}
    for p in persons:
        if p.get("transferred") and p.get("xref"):
            by_wid[wd_id_of[p["pid"]]]["legacySuccessFactorsId"] = sf_id_of[p["pid"]]
    leads = [w["id"] for w in wd_workers[:20]]
    for w in wd_workers[20:]:
        w["manager"] = {"id": r.choice(leads)}
    for w in wd_workers[:20]:
        w["manager"] = {"id": wd_workers[0]["id"]} if w is not wd_workers[0] else None
    # planted: orphan manager reference, a manager loop, workers without a job profile
    wd_workers[40]["manager"] = {"id": "W99999"}
    g.defects.append({"check": "manager_missing", "object": wd_workers[40]["id"]})
    a, b = wd_workers[5], wd_workers[6]
    a["manager"], b["manager"] = {"id": b["id"]}, {"id": a["id"]}
    g.defects.append({"check": "manager_loop", "object": "|".join(sorted([a["id"], b["id"]]))})
    staffed = {(w["jobProfile"] or {}).get("id") for w in wd_workers}
    for e in report_entries:
        if e["Job_Profile_ID"] not in staffed and e["Job_Profile_ID"] not in {d["jobs"][1] for d in dup_jobs}:
            g.defects.append({"check": "job_without_incumbents", "object": e["Job_Profile_ID"]})
    for idx in (77, 141):
        wd_workers[idx]["jobProfile"] = None
        g.defects.append({"check": "worker_without_job", "object": wd_workers[idx]["id"]})

    # current skills already on Workday worker profiles (some typed by employees, some from an earlier sync)
    for p in persons:
        wid = wd_id_of.get(p["pid"])
        if not wid:
            continue
        if r.random() < 0.3:
            manual = r.choice(["Teamwork", "Communication", "Python", "Leadership", "Excel", "Problem solving", "Projektmanagement"])
            wd_skills_current.append({"worker": wid, "skill": manual, "skillId": None, "source": "employee"})
        if r.random() < 0.25:
            sid = r.choice(p["true"] + [r.choice(all_ids)])
            wd_skills_current.append({"worker": wid, "skill": g.skills[sid][1], "skillId": sid, "source": "skills-layer"})

    # Keldorf free-text profile (aboutMe) in SF: skills, aspirations, planted sensitive data
    sens_iter = iter(SENSITIVE)
    for n, p in enumerate([p for p in persons if p["company"] == "keldorf"]):
        if n % 2:
            continue
        tid = f"about:{sf_id_of[p['pid']]}"
        lang = "de" if r.random() < 0.8 else "en"
        mentioned = r.sample(p["true"], k=min(len(p["true"]), r.randint(1, 3)))
        aspire = g.other_skill(set(p["true"])) if r.random() < 0.6 else None
        sens = None
        if n % 9 == 0:
            item = next(sens_iter, None)
            if item:
                sens = item[1]
                g.defects.append({"check": f"sensitive_free_text:{item[0]}", "object": sf_id_of[p["pid"]]})
        sf_profiles.append({"userId": sf_id_of[p["pid"]], "aboutMe": g.about_text(tid, lang, mentioned, aspire, sens), "language": lang})

    # ----------------------------------------------------------- Jira (engineering and digital people)
    jira_users, jira_issues = [], []
    eng_roles = {"electrical-engineer", "battery-engineer", "automation-engineer", "mechanical-engineer", "software-engineer",
                 "embedded-engineer", "platform-engineer", "data-engineer", "data-scientist", "quality-engineer",
                 "security-engineer", "technical-writer", "process-engineer", "maintenance-technician"}
    issue_no = 0
    for p in persons:
        if p["role"] not in eng_roles:
            continue
        acc = f"712020:{r.getrandbits(64):016x}"
        dom = "keldorf.example" if p["company"] == "keldorf" and not p.get("transferred") else "norvane.example"
        hidden = r.random() < 0.35  # Jira Cloud hides email unless the user's profile visibility allows it
        disp = f"{p['first']} {p['last']}"
        if hidden and r.random() < 0.25:
            disp = f"{p['first'][0]}. {p['last']}"
        jira_users.append({"accountId": acc, "displayName": disp, "emailAddress": None if hidden else email(p["first"], p["last"], dom), "active": True})
        gold_identity[f"jira:{acc}"] = p["pid"]
        lang_pool = ["en"] * 6 + (["de"] * 3 if p["company"] == "keldorf" else ["nl"] * 2)
        for _ in range(r.randint(2, 14)):
            issue_no += 1
            key = f"ELEC-{1000 + issue_no}"
            sid = r.choice(p["true"]) if r.random() < 0.82 else r.choice(all_ids)
            if g.skills[sid][6]:  # ambiguous skills: write the canonical name so the label stays exact
                sid = r.choice(p["true"])
            lang = r.choice(lang_pool)
            if lang == "nl" and lang not in TICKET:
                lang = "en"
            text = g.ticket_text(key, lang, sid)
            resolved = AS_OF - timedelta(days=r.randint(5, 1400))
            jira_issues.append({"key": key, "fields": {"summary": text, "assignee": {"accountId": acc}, "status": {"name": "Done"},
                                                         "resolutiondate": f"{resolved.isoformat()}T10:00:00.000+0000",
                                                         "components": [{"name": g.skills[sid][2]}], "labels": []}})
    # planted: three Jira accounts nobody can be resolved to (contractors)
    for n in range(3):
        acc = f"712020:{r.getrandbits(64):016x}"
        jira_users.append({"accountId": acc, "displayName": f"Contractor {n + 1}", "emailAddress": None, "active": True})
        gold_identity[f"jira:{acc}"] = "external"
        g.defects.append({"check": "jira_account_unresolved", "object": acc})

    # ----------------------------------------------------------- LMS completions (CSV)
    courses: dict[tuple[str, str], str] = {}
    lms_rows = []
    for p in persons:
        lang = {"norvane": r.choice(["en", "nl", "nl", "fr"]), "keldorf": r.choice(["de", "de", "en"])}[p["company"]]
        for _ in range(r.randint(0, 4)):
            sid = r.choice(p["true"]) if r.random() < 0.6 else g.other_skill(set(p["true"]))
            ck = (sid, lang)
            if ck not in courses:
                cid = f"C-{len(courses) + 1:03d}"
                courses[ck] = cid
                title = g.course_text(f"course:{cid}", lang, sid)
                courses[(cid, "title")] = title
            cid = courses[ck]
            ident = email(p["first"], p["last"], "norvane.example" if p["company"] == "norvane" or p.get("transferred") else "keldorf.example")
            lms_rows.append([ident, cid, courses[(cid, "title")], (AS_OF - timedelta(days=r.randint(10, 1200))).isoformat()])
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["learner_email", "course_id", "course_title", "completed_on"])
    w.writerows(sorted(lms_rows))

    # ----------------------------------------------------------- customer skill libraries (for the crosswalk)
    wd_library, sf_library, gold_cross = [], [], {}
    messy = {"SK-015": ["python", "Python programming", "Python (advanced)"], "SK-043": ["Project Mgmt", "projectmanagement", "PM"],
             "SK-030": ["MS Excel", "excel"], "SK-049": ["Leadership", "People leadership"], "SK-012": ["Lassen (TIG)", "welding"],
             "SK-026": ["Azure cloud", "MS Azure"], "SK-041": ["VCA", "Safety"], "SK-024": ["Kubernetes (K8S)"],
             "SK-004": ["PLC (Siemens)", "PLC"], "SK-052": ["Klantvriendelijkheid"], "SK-055": ["Analytical thinking"],
             "SK-029": ["PowerBI"], "SK-036": ["S&OP planning"], "SK-034": ["Lean Six Sigma Green Belt"]}
    unmappable = ["Teamwork", "Communication", "Problem solving", "Flexibility", "Punctuality", "Dutch", "French", "German", "Driving licence B"]
    n = 0
    for sid, forms in messy.items():
        for form in forms:
            n += 1
            wd_library.append({"Skill_ID": f"WDS-{n:03d}", "Skill_Name": form})
            gold_cross[f"workday:WDS-{n:03d}"] = sid
    for sid in r.sample(all_ids, 22):
        n += 1
        wd_library.append({"Skill_ID": f"WDS-{n:03d}", "Skill_Name": g.skills[sid][1]})
        gold_cross[f"workday:WDS-{n:03d}"] = sid
    for form in unmappable:
        n += 1
        wd_library.append({"Skill_ID": f"WDS-{n:03d}", "Skill_Name": form})
        gold_cross[f"workday:WDS-{n:03d}"] = None
    m = 0
    for sid, _, _, _, neutral, aliases, _, _ in T:
        if r.random() < 0.55:
            m += 1
            de = aliases.get("de") or [g.skills[sid][1]]
            sf_library.append({"externalCode": f"KDC-{m:03d}", "name_de_DE": de[0], "name_en_US": g.skills[sid][1] if r.random() < 0.4 else None})
            gold_cross[f"successfactors:KDC-{m:03d}"] = sid
    for form in ["Teamfähigkeit", "Belastbarkeit", "Führerschein Klasse B", "Englisch verhandlungssicher", "Zuverlässigkeit"]:
        m += 1
        sf_library.append({"externalCode": f"KDC-{m:03d}", "name_de_DE": form, "name_en_US": None})
        gold_cross[f"successfactors:KDC-{m:03d}"] = None

    # ----------------------------------------------------------- write
    gold_persons = {p["pid"]: {"skills": p["true"], "company": p["company"], "role": p["role"],
                               "workday": wd_id_of.get(p["pid"]), "successfactors": sf_id_of.get(p["pid"])} for p in persons}
    files = {
        "taxonomy.json": out["taxonomy.json"],
        "sources/workday/job_profiles.json": {"Report_Entry": report_entries},
        "sources/workday/workers.json": wd_workers,
        "sources/workday/worker_skills.json": wd_skills_current,
        "sources/workday/skills_library.json": {"Report_Entry": wd_library},
        "sources/successfactors/User.json": sf_users,
        "sources/successfactors/EmpJob.json": sf_empjob,
        "sources/successfactors/FOJobCode.json": sf_jobcodes,
        "sources/successfactors/cust_AboutMe.json": sf_profiles,
        "sources/successfactors/competency_library.json": sf_library,
        "sources/jira/users.json": jira_users,
        "sources/jira/issues.json": jira_issues,
        "sources/consent/optouts.json": {"exported": AS_OF.isoformat(),
                                         "workday": sorted(wd_id_of[p] for p in optouts if p in wd_id_of),
                                         "successfactors": sorted(sf_id_of[p] for p in optouts if p in sf_id_of)},
        "gold/identity.json": gold_identity,
        "gold/optouts.json": optouts,
        "gold/texts.json": g.texts,
        "gold/persons.json": gold_persons,
        "gold/defects.json": sorted(g.defects, key=lambda d: (d["check"], d["object"])),
        "gold/crosswalk.json": gold_cross,
    }
    rendered = {k: json.dumps(v, ensure_ascii=False, indent=1) + "\n" for k, v in files.items()}
    rendered["sources/lms/completions.csv"] = buf.getvalue()
    return rendered


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files = build()
    stale = []
    for rel, content in files.items():
        p = DATA / rel
        if args.check:
            if not p.exists() or p.read_text(encoding="utf-8") != content:
                stale.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
    if args.check:
        for s in stale:
            print("stale:", s)
        print("data is reproducible" if not stale else "run: python3 scripts/make_data.py")
        return 1 if stale else 0
    print(f"wrote {len(files)} files to data/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
