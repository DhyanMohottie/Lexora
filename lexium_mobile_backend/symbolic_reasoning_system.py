import re
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd


@dataclass
class Citation:
    statute: str
    section: str = None
    article: str = None

    def __str__(self):
        parts = [self.statute]
        if self.section:
            parts.append(f"Section {self.section}")
        if self.article:
            parts.append(f"Article {self.article}")
        return ", ".join(parts)


@dataclass
class LegalClaim:
    text: str
    citations: List[Citation]
    claim_type: str = "general"


@dataclass
class ValidationResult:
    is_valid: bool
    confidence: float
    violations: List[str]
    satisfied_rules: List[str]
    explanation: str


# ── Abbreviation / alias map for Sri Lankan statutes ─────────────────────────
ABBREVIATION_MAP = {
    'cpc':                          'Civil Procedure Code',
    'crc':                          'Criminal Procedure Code',
    'pc':                           'Penal Code',
    'ea':                           'Evidence Act',
    'eo':                           'Evidence Ordinance',
    'laa':                          'Land Acquisition Act',
    'cogsa':                        'Carriage of Goods by Sea Act',
    'constitution':                 'Constitution of Sri Lanka',
    'the constitution':             'Constitution of Sri Lanka',
    'penal code':                   'Penal Code',
    'civil procedure code':         'Civil Procedure Code',
    'criminal procedure code':      'Criminal Procedure Code',
    'evidence ordinance':           'Evidence Ordinance',
    'evidence act':                 'Evidence Ordinance',
    'rent act':                     'Rent Act',
    'judicature act':               'Judicature Act',
    'establishment code':           'Establishment Code',
    'interpretation ordinance':     'Interpretation Ordinance',
    'administration of justice law':'Administration of Justice Law',
    'land acquisition act':         'Land Acquisition Act',
    'motor traffic act':            'Motor Traffic Act',
    'inland revenue':               'Inland Revenue Act',
    'prevention of terrorism':      'Prevention of Terrorism Act',
    'public security':              'Public Security Ordinance',
    'shop and office':              'Shop and Office Employees Act',
    'termination of employment':    'Termination of Employment of Workmen Act',
    'budgetary relief':             'Budgetary Relief Allowance of Workers Act',
    'registration of documents':    'Registration of Documents Ordinance',
    'partition':                    'Partition Law',
    'prescription ordinance':       'Prescription Ordinance',
    'recovery of loans':            'Recovery of Loans by Banks Act',
    'debt recovery':                'Debt Recovery Act',
    'universities act':             'Universities Act',
    'companies act':                'Companies Act',
    'navy act':                     'Navy Act',
    'army act':                     'Army Act',
    'immigration':                  'Immigration and Emigration Act',
    'citizenship':                  'Citizenship Act',
    'parliamentary elections':      'Parliamentary Elections Act',
    'provincial councils':          'Provincial Councils Act',
    'municipal councils':           'Municipal Councils Ordinance',
    'urban councils':               'Urban Councils Ordinance',
}

# Words that indicate the sentence is giving legal advice
ADVICE_WORDS = {
    'should', 'must', 'can', 'may', 'could', 'would', 'shall',
    'file', 'apply', 'petition', 'seek', 'invoke', 'pursue',
    'claim', 'challenge', 'appeal', 'refer', 'consult',
    'approach', 'consider', 'utilize', 'use', 'rely',
    'entitled', 'allowed', 'permitted', 'required', 'obligated',
    'recommend', 'advised', 'suggest', 'pursuant', 'under',
    'according', 'provided', 'stipulated', 'governed',
}


def normalize_statute_name(name: str) -> str:
    """Normalize statute name for fuzzy matching."""
    name = name.lower().strip()
    name = re.sub(r',?\s*\d{4}', '', name)
    name = re.sub(r'no\.?\s*\d+\s*(of\s*\d+)?', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def fuzzy_match_statute(extracted: str, valid_statutes: set) -> Optional[str]:
    """
    Match extracted statute name to KB using 5-level fuzzy matching:
    1. Abbreviation map
    2. Exact normalized match
    3. Substring match
    4. Suffix variation (Act vs Ordinance vs Code vs Law)
    5. Word overlap (2+ significant words)
    """
    if not extracted:
        return None

    norm = normalize_statute_name(extracted)

    # 1. Abbreviation map
    if norm in ABBREVIATION_MAP:
        candidate = ABBREVIATION_MAP[norm]
        for vs in valid_statutes:
            if candidate.lower() in vs.lower() or vs.lower() in candidate.lower():
                return vs
        return candidate

    # 2. Exact normalized match
    for vs in valid_statutes:
        if normalize_statute_name(vs) == norm:
            return vs

    # 3. Substring match
    for vs in valid_statutes:
        vs_norm = normalize_statute_name(vs)
        if norm in vs_norm or vs_norm in norm:
            return vs

    # 4. Suffix variation
    suffixes = ['act', 'ordinance', 'code', 'law', 'rules', 'order']
    base = norm
    for suffix in suffixes:
        base = re.sub(rf'\b{suffix}\b', '', base).strip()

    if len(base) > 4:
        for vs in valid_statutes:
            vs_base = normalize_statute_name(vs)
            for suffix in suffixes:
                vs_base = re.sub(rf'\b{suffix}\b', '', vs_base).strip()
            if base in vs_base or vs_base in base:
                return vs

    # 5. Word overlap (2+ significant words)
    norm_words = set(w for w in norm.split() if len(w) > 3)
    best_match, best_score = None, 0
    for vs in valid_statutes:
        vs_words = set(w for w in normalize_statute_name(vs).split() if len(w) > 3)
        overlap = len(norm_words & vs_words)
        if overlap >= 2 and overlap > best_score:
            best_score = overlap
            best_match = vs

    return best_match


class CitationExtractor:
    """
    Two-pass statute extractor with fuzzy matching and
    special handling for Constitution, abbreviations, and
    Establishment Code.
    """

    _PAT_STRICT = re.compile(
        r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*'
        r'\s+(?:Act|Ordinance|Code|Rules|Law)'
        r'(?:\s+No\.?\s*[\d\.]+)?)'
    )
    _PAT_CONNECTOR = re.compile(
        r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*'
        r'\s+(?:of|and|for)'
        r'\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*'
        r'\s+(?:Act|Ordinance|Code|Rules|Law)'
        r'(?:\s+No\.?\s*[\d\.]+)?)'
    )
    _PAT_YEAR_ACT  = re.compile(r'(\d{4}\s+Act)')

    # Constitution only when used as a legal reference
    _PAT_CONST = re.compile(
        r'(?:'
        r'Article\s+\d+[A-Za-z]?\s*(?:\([^)]+\))?\s+of\s+the\s+Constitution'
        r'|under\s+(?:the\s+)?Constitution'
        r'|the\s+Constitution\s+of\s+Sri\s+Lanka'
        r'|Constitution\s+of\s+the\s+Republic'
        r'|pursuant\s+to\s+the\s+Constitution'
        r')',
        re.IGNORECASE
    )

    _PAT_ABBREV    = re.compile(r'\b(CPC|CRC|PC|EA|EO|LAA|COGSA)\b')
    _PAT_ESTABLISH = re.compile(r'\b(Establishment\s+Code)\b', re.IGNORECASE)
    _GARBAGE       = re.compile(r'^[A-Za-z]\s+(?:of\s+(?:the\s+)?|the\s+)?')
    _PAT_SECT      = re.compile(r'[Ss]ection\s+([\d]+(?:\([^\)]+\))*)')
    _PAT_ART       = re.compile(r'Article\s+(\d+)')

    def _clean(self, s: str) -> str:
        return self._GARBAGE.sub('', s.strip()).strip()

    def _dedup(self, statutes: List[str]) -> List[str]:
        statutes = sorted(set(statutes), key=len, reverse=True)
        result = []
        for s in statutes:
            if not any(s in longer for longer in result):
                result.append(s)
        return result

    def extract_statutes(self, text: str) -> List[str]:
        found = []

        # Connector pass
        for s in self._PAT_CONNECTOR.findall(text):
            c = self._clean(s)
            if len(c) > 5:
                found.append(c)

        # Strict pass
        for s in self._PAT_STRICT.findall(text):
            c = self._clean(s)
            if len(c) > 5:
                found.append(c)

        # Constitution — only when used as legal reference
        if self._PAT_CONST.search(text):
            found.append('Constitution of Sri Lanka')

        # Abbreviations
        for abbrev in self._PAT_ABBREV.findall(text):
            mapped = ABBREVIATION_MAP.get(abbrev.lower())
            if mapped:
                found.append(mapped)

        # Establishment Code
        if self._PAT_ESTABLISH.search(text):
            found.append('Establishment Code')

        # Year acts
        for s in self._PAT_YEAR_ACT.findall(text):
            if s not in found:
                found.append(s)

        return self._dedup(found)

    def extract(self, text: str) -> List[Citation]:
        citations = []
        statutes  = self.extract_statutes(text)
        sections  = self._PAT_SECT.findall(text)
        articles  = self._PAT_ART.findall(text)

        if statutes:
            for statute in statutes:
                citations.append(Citation(
                    statute=statute,
                    section=sections[0] if sections else None,
                    article=articles[0] if articles else None,
                ))
        elif sections:
            for section in sections:
                citations.append(Citation(statute="Unknown", section=section))
        return citations


class LegalKnowledgeBase:

    def __init__(self, statutes_df=None, sections_df=None):
        self.valid_statutes: set = set()
        if statutes_df is not None:
            self.valid_statutes = set(statutes_df['statute'].unique())
        self.valid_sections: set = set()
        if sections_df is not None:
            self.valid_sections = set(sections_df['section'].unique())
        self.co_occurrence: Dict[tuple, int] = {}
        if statutes_df is not None:
            self._build_co_occurrence(statutes_df)

        self.legal_keywords = {
            'court', 'judge', 'jury', 'plaintiff', 'defendant',
            'statute', 'law', 'section', 'article', 'act',
            'precedent', 'ruling', 'verdict', 'appeal', 'motion',
            'evidence', 'testimony', 'witness', 'counsel', 'attorney',
            'jurisdiction', 'constitution', 'ordinance', 'petition',
            'respondent', 'appellant', 'judgment', 'order', 'writ',
            'liable', 'damages', 'remedy', 'relief', 'injunction',
        }

    def _build_co_occurrence(self, statutes_df: pd.DataFrame):
        for _doc_id, group in statutes_df.groupby('document_id'):
            statutes = group['statute'].tolist()
            for i, s1 in enumerate(statutes):
                for s2 in statutes[i + 1:]:
                    key = tuple(sorted([s1, s2]))
                    self.co_occurrence[key] = self.co_occurrence.get(key, 0) + 1

    def is_valid_statute(self, statute: str) -> bool:
        if statute in self.valid_statutes:
            return True
        return fuzzy_match_statute(statute, self.valid_statutes) is not None

    def is_valid_section(self, section: str) -> bool:
        return section in self.valid_sections

    def statutes_co_occur(self, statute1: str, statute2: str) -> bool:
        key = tuple(sorted([statute1, statute2]))
        return self.co_occurrence.get(key, 0) > 0

    def count_legal_keywords(self, text: str) -> int:
        tl = text.lower()
        return sum(1 for kw in self.legal_keywords if kw in tl)

    def count_advice_words(self, text: str) -> int:
        tl = text.lower().split()
        return sum(1 for w in tl if w in ADVICE_WORDS)


class SymbolicRulesEngine:

    def __init__(self, knowledge_base: LegalKnowledgeBase):
        self.kb    = knowledge_base
        self.rules = self._define_rules()

    def _define_rules(self) -> Dict[str, callable]:
        return {
            # ── Core legal reference checks ──────────────────────────────
            'has_legal_reference':  lambda claim: (
                                        len(claim.citations) > 0
                                        or bool(re.search(r'[Ss]ection\s+\d+|Article\s+\d+', claim.text))
                                    ),
            'reference_is_valid':   lambda claim: (
                                        len(claim.citations) > 0 and
                                        all(self.kb.is_valid_statute(c.statute)
                                            for c in claim.citations
                                            if c.statute != 'Unknown')
                                    ),
            'specific_enough':      lambda claim: (
                                        bool(re.search(r'[Ss]ection\s+\d+', claim.text))
                                        or bool(re.search(r'Article\s+\d+', claim.text))
                                        or len(claim.citations) >= 1
                                    ),

            # ── Advice quality checks ────────────────────────────────────
            'actionable_language':  lambda claim: (
                                        self.kb.count_advice_words(claim.text) >= 1
                                    ),
            'legal_context':        lambda claim: (
                                        self.kb.count_legal_keywords(claim.text) >= 2
                                    ),

            # ── Basic quality checks ─────────────────────────────────────
            'minimum_length':       lambda claim: len(claim.text.split()) >= 8,
            'not_gibberish':        lambda claim: not self._is_gibberish(claim.text),
            'logical_consistency':  lambda claim: self._check_consistency(claim.text),
            'no_unknown_citations': lambda claim: all(
                                        c.statute != 'Unknown'
                                        for c in claim.citations
                                    ),
            'coherent_reference':   lambda claim: self._check_coherence(claim),
        }

    def _check_coherence(self, claim: LegalClaim) -> bool:
        """Citations should co-occur in real documents if multiple exist."""
        if len(claim.citations) < 2:
            return True
        cits = [c.statute for c in claim.citations]
        for i in range(len(cits) - 1):
            if not self.kb.statutes_co_occur(cits[i], cits[i + 1]):
                return False
        return True

    def _is_gibberish(self, text: str) -> bool:
        if len(text.split()) < 3:
            return True
        # Keyboard spam
        if any(p in text.lower() for p in ['asdf', 'qwer', 'zxcv', 'jkl;']):
            return True
        # Mostly numbers
        words = text.split()
        num_count = sum(1 for w in words if re.match(r'^\d+$', w))
        if num_count / len(words) > 0.6:
            return True
        return False

    def _check_consistency(self, text: str) -> bool:
        contradictions = [
            ('valid', 'invalid'),
            ('guilty', 'innocent'),
            ('true', 'false'),
            ('legal', 'illegal'),
            ('allowed', 'prohibited'),
        ]
        tl = text.lower()
        return not any(w1 in tl and w2 in tl for w1, w2 in contradictions)

    def evaluate(self, claim: LegalClaim) -> ValidationResult:
        rule_weights = {
            'has_legal_reference':  0.25,   # most important — must cite something
            'reference_is_valid':   0.20,   # citation must be real
            'actionable_language':  0.15,   # must be giving advice
            'specific_enough':      0.12,   # must be specific (section/article)
            'legal_context':        0.12,   # must use legal terminology
            'minimum_length':       0.06,   # must be a complete sentence
            'not_gibberish':        0.05,   # must not be spam
            'logical_consistency':  0.03,   # must not contradict itself
            'no_unknown_citations': 0.01,   # citations should be named
            'coherent_reference':   0.01,   # citations should co-occur
        }

        satisfied, violations = [], []
        weighted_score = 0.0

        for name, func in self.rules.items():
            try:
                passed = func(claim)
                if passed:
                    satisfied.append(name)
                    weighted_score += rule_weights.get(name, 0.05)
                else:
                    violations.append(name)
            except Exception as e:
                violations.append(f"{name} (error: {e})")

        # Partial credit — keyword density bonus
        keyword_count = self.kb.count_legal_keywords(claim.text)
        keyword_bonus = min(0.05, keyword_count * 0.005)
        weighted_score = min(1.0, weighted_score + keyword_bonus)

        # Advice word bonus
        advice_count = self.kb.count_advice_words(claim.text)
        advice_bonus = min(0.03, advice_count * 0.01)
        weighted_score = min(1.0, weighted_score + advice_bonus)

        # Rescale to [0.10, 0.95] so full range is reachable
        confidence = 0.10 + (weighted_score * 0.85)
        confidence = round(min(0.95, max(0.10, confidence)), 4)

        is_valid    = confidence >= 0.60
        explanation = self._generate_explanation(
            is_valid, satisfied, violations, confidence)

        return ValidationResult(
            is_valid=is_valid, confidence=confidence,
            violations=violations, satisfied_rules=satisfied,
            explanation=explanation,
        )

    def _generate_explanation(self, is_valid, satisfied, violations, confidence):
        if is_valid:
            exp  = f" VALID (Confidence: {confidence:.1%})\n\n"
            exp += f"Satisfied {len(satisfied)}/{len(self.rules)} rules:\n"
            for r in satisfied:
                exp += f"   ✓ {r.replace('_', ' ').title()}\n"
            if violations:
                exp += f"\nMinor issues ({len(violations)}):\n"
                for r in violations:
                    exp += f"   ✗ {r.replace('_', ' ').title()}\n"
        else:
            exp  = f" INVALID (Confidence: {confidence:.1%})\n\n"
            exp += f"Rule violations ({len(violations)}):\n"
            for r in violations:
                exp += f"   ✗ {r.replace('_', ' ').title()}\n"
            if satisfied:
                exp += f"\nSatisfied rules ({len(satisfied)}):\n"
                for r in satisfied[:3]:
                    exp += f"   ✓ {r.replace('_', ' ').title()}\n"
        return exp


class SymbolicReasoningSystem:

    def __init__(self, statutes_df=None, sections_df=None):
        self.citation_extractor = CitationExtractor()
        self.knowledge_base     = LegalKnowledgeBase(statutes_df, sections_df)
        self.rules_engine       = SymbolicRulesEngine(self.knowledge_base)

    def validate(self, text: str) -> ValidationResult:
        citations = self.citation_extractor.extract(text)
        claim     = LegalClaim(text=text, citations=citations)
        return self.rules_engine.evaluate(claim)

    def batch_validate(self, texts: List[str]) -> List[ValidationResult]:
        return [self.validate(t) for t in texts]


def _auto_load() -> SymbolicReasoningSystem:
    statutes_df = sections_df = None
    for path in ['data/statutes.csv', './statutes.csv', '../data/statutes.csv', 'statutes.csv']:
        if os.path.exists(path):
            statutes_df = pd.read_csv(path)
            break
    for path in ['data/sections.csv', './sections.csv', '../data/sections.csv', 'sections.csv']:
        if os.path.exists(path):
            sections_df = pd.read_csv(path)
            break
    return SymbolicReasoningSystem(statutes_df, sections_df)


_SYSTEM = _auto_load()

def validate_claim(text: str) -> ValidationResult:
    return _SYSTEM.validate(text)

def validate_multiple(texts: List[str]) -> List[ValidationResult]:
    return _SYSTEM.batch_validate(texts)

def get_system() -> SymbolicReasoningSystem:
    return _SYSTEM