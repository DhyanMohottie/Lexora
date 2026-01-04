import re
import os
from typing import List, Dict
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


class CitationExtractor:
    
    def __init__(self):
        self.patterns = {
            'section': r'Section\s+(\d+)',
            'article': r'Article\s+(\d+)',
            'statute': r'([A-Z][a-z]+\s+Act)',
            'act': r'(\d{4}\s+Act)',
        }
    
    def extract(self, text: str) -> List[Citation]:
        citations = []
        statutes = re.findall(self.patterns['statute'], text)
        statutes += re.findall(self.patterns['act'], text)
        sections = re.findall(self.patterns['section'], text)
        articles = re.findall(self.patterns['article'], text)
        
        if statutes:
            for statute in statutes:
                citation = Citation(
                    statute=statute,
                    section=sections[0] if sections else None,
                    article=articles[0] if articles else None
                )
                citations.append(citation)
        elif sections:
            for section in sections:
                citation = Citation(statute="Unknown", section=section)
                citations.append(citation)
        
        return citations


class LegalKnowledgeBase:
    
    def __init__(self, statutes_df=None, sections_df=None):
        self.valid_statutes = set()
        if statutes_df is not None:
            self.valid_statutes = set(statutes_df['statute'].unique())
        
        self.valid_sections = set()
        if sections_df is not None:
            self.valid_sections = set(sections_df['section'].unique())
        
        self.co_occurrence = {}
        if statutes_df is not None:
            self._build_co_occurrence(statutes_df)
        
        self.legal_keywords = {
            'court', 'judge', 'jury', 'plaintiff', 'defendant',
            'statute', 'law', 'section', 'article', 'act',
            'precedent', 'ruling', 'verdict', 'appeal', 'motion',
            'evidence', 'testimony', 'witness', 'counsel', 'attorney'
        }
    
    def _build_co_occurrence(self, statutes_df):
        for doc_id, group in statutes_df.groupby('document_id'):
            statutes = group['statute'].tolist()
            for i, stat1 in enumerate(statutes):
                for stat2 in statutes[i+1:]:
                    key = tuple(sorted([stat1, stat2]))
                    self.co_occurrence[key] = self.co_occurrence.get(key, 0) + 1
    
    def is_valid_statute(self, statute: str) -> bool:
        return statute in self.valid_statutes
    
    def is_valid_section(self, section: str) -> bool:
        return section in self.valid_sections
    
    def statutes_co_occur(self, statute1: str, statute2: str) -> bool:
        key = tuple(sorted([statute1, statute2]))
        return self.co_occurrence.get(key, 0) > 0
    
    def count_legal_keywords(self, text: str) -> int:
        text_lower = text.lower()
        return sum(1 for keyword in self.legal_keywords if keyword in text_lower)


class SymbolicRulesEngine:
    
    def __init__(self, knowledge_base: LegalKnowledgeBase):
        self.kb = knowledge_base
        self.rules = self._define_rules()
    
    def _define_rules(self) -> Dict[str, callable]:
        return {
            'citation_exists': lambda claim: len(claim.citations) > 0,
            'citations_valid': lambda claim: all(
                self.kb.is_valid_statute(c.statute) for c in claim.citations
            ),
            'sufficient_citations': lambda claim: len(claim.citations) >= 2,
            'legal_language': lambda claim: self.kb.count_legal_keywords(claim.text) >= 2,
            'proper_format': lambda claim: all(
                c.statute != "Unknown" for c in claim.citations
            ),
            'citation_coherence': lambda claim: self._check_coherence(claim),
            'minimum_length': lambda claim: len(claim.text.split()) >= 5,
            'not_gibberish': lambda claim: not self._is_gibberish(claim.text),
            'logical_consistency': lambda claim: self._check_consistency(claim.text),
            'complete_claim': lambda claim: self._is_complete(claim),
        }
    
    def _check_coherence(self, claim: LegalClaim) -> bool:
        if len(claim.citations) < 2:
            return True
        citations = [c.statute for c in claim.citations]
        for i in range(len(citations) - 1):
            if not self.kb.statutes_co_occur(citations[i], citations[i+1]):
                return False
        return True
    
    def _is_gibberish(self, text: str) -> bool:
        words = text.split()
        if len(words) < 3:
            return True
        random_patterns = ['asdf', 'qwer', 'zxcv', 'jkl;']
        return any(pattern in text.lower() for pattern in random_patterns)
    
    def _check_consistency(self, text: str) -> bool:
        contradictions = [
            ('valid', 'invalid'),
            ('guilty', 'innocent'),
            ('true', 'false'),
        ]
        text_lower = text.lower()
        for word1, word2 in contradictions:
            if word1 in text_lower and word2 in text_lower:
                return False
        return True
    
    def _is_complete(self, claim: LegalClaim) -> bool:
        return len(claim.citations) > 0 and len(claim.text.split()) >= 10
    
    def evaluate(self, claim: LegalClaim) -> ValidationResult:
        satisfied = []
        violations = []
        
        for rule_name, rule_func in self.rules.items():
            try:
                if rule_func(claim):
                    satisfied.append(rule_name)
                else:
                    violations.append(rule_name)
            except Exception as e:
                violations.append(f"{rule_name} (error: {e})")
        
        total_rules = len(self.rules)
        satisfied_count = len(satisfied)
        confidence = satisfied_count / total_rules
        is_valid = confidence >= 0.7
        explanation = self._generate_explanation(is_valid, satisfied, violations, confidence)
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            violations=violations,
            satisfied_rules=satisfied,
            explanation=explanation
        )
    
    def _generate_explanation(self, is_valid: bool, satisfied: List[str], 
                            violations: List[str], confidence: float) -> str:
        if is_valid:
            explanation = f" VALID (Confidence: {confidence:.1%})\n\n"
            explanation += f"Satisfied {len(satisfied)}/{len(self.rules)} rules:\n"
            for rule in satisfied:
                explanation += f"   {rule.replace('_', ' ').title()}\n"
            if violations:
                explanation += f"\nMinor issues ({len(violations)}):\n"
                for rule in violations:
                    explanation += f"   {rule.replace('_', ' ').title()}\n"
        else:
            explanation = f" INVALID (Confidence: {confidence:.1%})\n\n"
            explanation += f"Rule violations ({len(violations)}):\n"
            for rule in violations:
                explanation += f"   {rule.replace('_', ' ').title()}\n"
            if satisfied:
                explanation += f"\nSatisfied rules ({len(satisfied)}):\n"
                for rule in satisfied[:3]:
                    explanation += f"   {rule.replace('_', ' ').title()}\n"
        return explanation


class SymbolicReasoningSystem:
    
    def __init__(self, statutes_df: pd.DataFrame = None, sections_df: pd.DataFrame = None):
        self.citation_extractor = CitationExtractor()
        self.knowledge_base = LegalKnowledgeBase(statutes_df, sections_df)
        self.rules_engine = SymbolicRulesEngine(self.knowledge_base)
    
    def validate(self, text: str) -> ValidationResult:
        citations = self.citation_extractor.extract(text)
        claim = LegalClaim(text=text, citations=citations)
        result = self.rules_engine.evaluate(claim)
        return result
    
    def batch_validate(self, texts: List[str]) -> List[ValidationResult]:
        return [self.validate(text) for text in texts]


# Auto-load data and create system
def _auto_load():
    paths = ['data/statutes.csv', './statutes.csv', '../data/statutes.csv', 'statutes.csv']
    statutes_df, sections_df = None, None
    
    try:
        for path in paths:
            if os.path.exists(path):
                statutes_df = pd.read_csv(path)
                break
        
        paths = ['data/sections.csv', './sections.csv', '../data/sections.csv', 'sections.csv']
        for path in paths:
            if os.path.exists(path):
                sections_df = pd.read_csv(path)
                break
    except:
        pass
    
    return SymbolicReasoningSystem(statutes_df, sections_df)


_SYSTEM = _auto_load()


def validate_claim(text: str) -> ValidationResult:
    return _SYSTEM.validate(text)


def validate_multiple(texts: List[str]) -> List[ValidationResult]:
    return _SYSTEM.batch_validate(texts)


def get_system() -> SymbolicReasoningSystem:
    return _SYSTEM