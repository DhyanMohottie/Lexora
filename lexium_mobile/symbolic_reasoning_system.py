import subprocess
import tempfile
import re
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
import pandas as pd

print("=" * 70)
print("SYMBOLIC REASONING SYSTEM FOR LEGAL VALIDATION")
print("=" * 70)

@dataclass
class Citation:
    """Represents a legal citation"""
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
    """Represents a legal claim to validate"""
    text: str
    citations: List[Citation]
    claim_type: str = "general"  # general, procedural, substantive
    
@dataclass
class ValidationResult:
    """Result of symbolic validation"""
    is_valid: bool
    confidence: float
    violations: List[str]
    satisfied_rules: List[str]
    explanation: str


class CitationExtractor:
    """Extracts legal citations from text"""
    
    def __init__(self):
        # Regex patterns for different citation formats
        self.patterns = {
            'section': r'Section\s+(\d+)',
            'article': r'Article\s+(\d+)',
            'statute': r'([A-Z][a-z]+\s+Act)',
            'act': r'(\d{4}\s+Act)',
        }
    
    def extract(self, text: str) -> List[Citation]:
        """Extract citations from legal text"""
        citations = []
        
        # Find statutes/acts
        statutes = re.findall(self.patterns['statute'], text)
        statutes += re.findall(self.patterns['act'], text)
        
        # Find sections
        sections = re.findall(self.patterns['section'], text)
        
        # Find articles
        articles = re.findall(self.patterns['article'], text)
        
        # Combine into citations
        if statutes:
            for statute in statutes:
                citation = Citation(
                    statute=statute,
                    section=sections[0] if sections else None,
                    article=articles[0] if articles else None
                )
                citations.append(citation)
        elif sections:
            # Section without statute
            for section in sections:
                citation = Citation(statute="Unknown", section=section)
                citations.append(citation)
        
        return citations
    
    def count_citations(self, text: str) -> int:
        """Count total citations in text"""
        return len(self.extract(text))

print("✅ Citation Extractor defined")


#  LEGAL KNOWLEDGE BASE


class LegalKnowledgeBase:
    """Stores legal knowledge and corpus information"""
    
    def __init__(self, statutes_df=None, sections_df=None):
        # Valid statutes from corpus
        self.valid_statutes = set()
        if statutes_df is not None:
            self.valid_statutes = set(statutes_df['statute'].unique())
        
        # Valid sections from corpus
        self.valid_sections = set()
        if sections_df is not None:
            self.valid_sections = set(sections_df['section'].unique())
        
        # Citation co-occurrence patterns
        self.co_occurrence = {}
        if statutes_df is not None:
            self._build_co_occurrence(statutes_df)
        
        # Legal domain keywords
        self.legal_keywords = {
            'court', 'judge', 'jury', 'plaintiff', 'defendant',
            'statute', 'law', 'section', 'article', 'act',
            'precedent', 'ruling', 'verdict', 'appeal', 'motion',
            'evidence', 'testimony', 'witness', 'counsel', 'attorney'
        }
    
    def _build_co_occurrence(self, statutes_df):
        """Build citation co-occurrence patterns"""
        # Group by document
        for doc_id, group in statutes_df.groupby('document_id'):
            statutes = group['statute'].tolist()
            # Record which statutes appear together
            for i, stat1 in enumerate(statutes):
                for stat2 in statutes[i+1:]:
                    key = tuple(sorted([stat1, stat2]))
                    self.co_occurrence[key] = self.co_occurrence.get(key, 0) + 1
    
    def is_valid_statute(self, statute: str) -> bool:
        """Check if statute exists in corpus"""
        return statute in self.valid_statutes
    
    def is_valid_section(self, section: str) -> bool:
        """Check if section exists in corpus"""
        return section in self.valid_sections
    
    def statutes_co_occur(self, statute1: str, statute2: str) -> bool:
        """Check if two statutes commonly appear together"""
        key = tuple(sorted([statute1, statute2]))
        return self.co_occurrence.get(key, 0) > 0
    
    def count_legal_keywords(self, text: str) -> int:
        """Count legal keywords in text"""
        text_lower = text.lower()
        return sum(1 for keyword in self.legal_keywords if keyword in text_lower)

print("✅ Legal Knowledge Base defined")

#SYMBOLIC RULES ENGINE

class SymbolicRulesEngine:
    """
    Implements logical rules for legal validation
    Uses Answer Set Programming (ASP) logic
    """
    
    def __init__(self, knowledge_base: LegalKnowledgeBase):
        self.kb = knowledge_base
        self.rules = self._define_rules()
    
    def _define_rules(self) -> Dict[str, callable]:
        """Define validation rules"""
        return {
            # Rule 1: Citation Existence
            'citation_exists': lambda claim: len(claim.citations) > 0,
            
            # Rule 2: Valid Citations
            'citations_valid': lambda claim: all(
                self.kb.is_valid_statute(c.statute) for c in claim.citations
            ),
            
            # Rule 3: Sufficient Citations
            'sufficient_citations': lambda claim: len(claim.citations) >= 2,
            
            # Rule 4: Contains Legal Language
            'legal_language': lambda claim: self.kb.count_legal_keywords(claim.text) >= 2,
            
            # Rule 5: Proper Citation Format
            'proper_format': lambda claim: all(
                c.statute != "Unknown" for c in claim.citations
            ),
            
            # Rule 6: Citation Coherence (co-occurrence)
            'citation_coherence': lambda claim: self._check_coherence(claim),
            
            # Rule 7: Minimum Text Length
            'minimum_length': lambda claim: len(claim.text.split()) >= 5,
            
            # Rule 8: Not Gibberish
            'not_gibberish': lambda claim: not self._is_gibberish(claim.text),
            
            # Rule 9: Logical Consistency
            'logical_consistency': lambda claim: self._check_consistency(claim.text),
            
            # Rule 10: Complete Claim
            'complete_claim': lambda claim: self._is_complete(claim),
        }
    
    def _check_coherence(self, claim: LegalClaim) -> bool:
        """Check if citations make sense together"""
        if len(claim.citations) < 2:
            return True  # Single citation is always coherent
        
        # Check if citations commonly appear together
        citations = [c.statute for c in claim.citations]
        for i in range(len(citations) - 1):
            if not self.kb.statutes_co_occur(citations[i], citations[i+1]):
                return False
        return True
    
    def _is_gibberish(self, text: str) -> bool:
        """Check if text is gibberish"""
        words = text.split()
        if len(words) < 3:
            return True
        
        # Check for random character sequences
        random_patterns = ['asdf', 'qwer', 'zxcv', 'jkl;']
        return any(pattern in text.lower() for pattern in random_patterns)
    
    def _check_consistency(self, text: str) -> bool:
        """Check for logical consistency"""
        # Simple check: look for contradictions
        contradictions = [
            ('valid', 'invalid'),
            ('guilty', 'innocent'),
            ('true', 'false'),
        ]
        text_lower = text.lower()
        for word1, word2 in contradictions:
            if word1 in text_lower and word2 in text_lower:
                # Both contradictory terms present
                return False
        return True
    
    def _is_complete(self, claim: LegalClaim) -> bool:
        """Check if claim is complete"""
        # Must have citations and sufficient text
        return len(claim.citations) > 0 and len(claim.text.split()) >= 10
    
    def evaluate(self, claim: LegalClaim) -> ValidationResult:
        """
        Evaluate claim against all rules
        Returns validation result with explanations
        """
        satisfied = []
        violations = []
        
        # Check each rule
        for rule_name, rule_func in self.rules.items():
            try:
                if rule_func(claim):
                    satisfied.append(rule_name)
                else:
                    violations.append(rule_name)
            except Exception as e:
                violations.append(f"{rule_name} (error: {e})")
        
        # Calculate confidence
        total_rules = len(self.rules)
        satisfied_count = len(satisfied)
        confidence = satisfied_count / total_rules
        
        # Determine validity (threshold: 70%)
        is_valid = confidence >= 0.7
        
        # Generate explanation
        explanation = self._generate_explanation(
            is_valid, satisfied, violations, confidence
        )
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            violations=violations,
            satisfied_rules=satisfied,
            explanation=explanation
        )
    
    def _generate_explanation(
        self, 
        is_valid: bool, 
        satisfied: List[str], 
        violations: List[str],
        confidence: float
    ) -> str:
        """Generate human-readable explanation"""
        if is_valid:
            explanation = f"✅ VALID (Confidence: {confidence:.1%})\n\n"
            explanation += f"Satisfied {len(satisfied)}/{len(self.rules)} rules:\n"
            for rule in satisfied[:5]:  # Show top 5
                explanation += f"  ✓ {rule.replace('_', ' ').title()}\n"
            
            if violations:
                explanation += f"\nMinor issues ({len(violations)}):\n"
                for rule in violations[:3]:
                    explanation += f"  ⚠ {rule.replace('_', ' ').title()}\n"
        else:
            explanation = f"INVALID (Confidence: {confidence:.1%})\n\n"
            explanation += f"Rule violations ({len(violations)}):\n"
            for rule in violations:
                explanation += f"  ✗ {rule.replace('_', ' ').title()}\n"
            
            if satisfied:
                explanation += f"\nSatisfied rules ({len(satisfied)}):\n"
                for rule in satisfied[:3]:
                    explanation += f"  ✓ {rule.replace('_', ' ').title()}\n"
        
        return explanation

print("✅ Symbolic Rules Engine defined")

# ============================================================================
# PART 5: ASP (ANSWER SET PROGRAMMING) ENGINE
# ============================================================================

class ASPEngine:
    """
    Answer Set Programming engine using Clingo
    More advanced logical reasoning
    """
    
    def __init__(self):
        self.has_clingo = self._check_clingo()
    
    def _check_clingo(self) -> bool:
        """Check if Clingo is installed"""
        try:
            result = subprocess.run(
                ['clingo', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def solve(self, claim: LegalClaim, knowledge_base: LegalKnowledgeBase) -> Dict:
        """
        Solve using ASP (if available)
        Falls back to rule-based if Clingo not available
        """
        if not self.has_clingo:
            return {
                'valid': False,
                'message': 'Clingo not installed (optional)',
                'using_fallback': True
            }
        
        # Convert claim to ASP facts
        asp_program = self._generate_asp_program(claim, knowledge_base)
        
        # Solve with Clingo
        try:
            result = self._run_clingo(asp_program)
            return {
                'valid': result.get('SATISFIABLE', False),
                'models': result.get('models', []),
                'using_fallback': False
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'ASP error: {e}',
                'using_fallback': True
            }
    
    def _generate_asp_program(
        self, 
        claim: LegalClaim, 
        kb: LegalKnowledgeBase
    ) -> str:
        """Generate ASP program for claim"""
        program = "% Legal Claim Validation ASP Program\n\n"
        
        # Facts about the claim
        for i, citation in enumerate(claim.citations):
            program += f"citation({i}, \"{citation.statute}\").\n"
        
        # Facts about valid statutes
        for statute in list(kb.valid_statutes)[:10]:  # Limit for demo
            program += f"valid_statute(\"{statute}\").\n"
        
        # Rules
        program += """
% Rule: Citation must reference valid statute
invalid_citation(ID) :- citation(ID, Statute), not valid_statute(Statute).

% Rule: Claim is valid if no invalid citations
valid_claim :- not has_invalid_citation.
has_invalid_citation :- invalid_citation(_).

% Generate answer
#show valid_claim/0.
#show invalid_citation/1.
"""
        return program
    
    def _run_clingo(self, program: str) -> Dict:
        """Run Clingo solver"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lp', delete=False) as f:
            f.write(program)
            f.flush()
            
            result = subprocess.run(
                ['clingo', f.name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout
            return self._parse_clingo_output(output)
    
    def _parse_clingo_output(self, output: str) -> Dict:
        """Parse Clingo output"""
        models = []
        satisfiable = 'SATISFIABLE' in output
        
        # Extract answer sets
        for line in output.split('\n'):
            if line.startswith('Answer:'):
                continue
            elif 'valid_claim' in line or 'invalid_citation' in line:
                models.append(line.strip())
        
        return {
            'SATISFIABLE': satisfiable,
            'models': models
        }

print("✅ ASP Engine defined")

# ============================================================================
# PART 6: COMPLETE SYMBOLIC SYSTEM
# ============================================================================

class SymbolicReasoningSystem:
    """
    Complete symbolic reasoning system
    Combines rule-based logic and ASP
    """
    
    def __init__(
        self, 
        statutes_df: pd.DataFrame = None,
        sections_df: pd.DataFrame = None
    ):
        self.citation_extractor = CitationExtractor()
        self.knowledge_base = LegalKnowledgeBase(statutes_df, sections_df)
        self.rules_engine = SymbolicRulesEngine(self.knowledge_base)
        self.asp_engine = ASPEngine()
        
        print(f"✅ Symbolic System initialized")
        print(f"   Valid statutes: {len(self.knowledge_base.valid_statutes)}")
        print(f"   Valid sections: {len(self.knowledge_base.valid_sections)}")
        print(f"   ASP available: {self.asp_engine.has_clingo}")
    
    def validate(self, text: str) -> ValidationResult:
        """
        Main validation function
        Takes text, returns validation result
        """
        # Extract citations
        citations = self.citation_extractor.extract(text)
        
        # Create claim object
        claim = LegalClaim(text=text, citations=citations)
        
        # Rule-based validation
        result = self.rules_engine.evaluate(claim)
        
        # Optional: ASP validation (if available)
        if self.asp_engine.has_clingo:
            asp_result = self.asp_engine.solve(claim, self.knowledge_base)
            # Combine results
            if not asp_result.get('using_fallback', True):
                result.confidence = (result.confidence + float(asp_result['valid'])) / 2
                result.explanation += f"\n\nASP Reasoning: {'✅ Valid' if asp_result['valid'] else '❌ Invalid'}"
        
        return result
    
    def batch_validate(self, texts: List[str]) -> List[ValidationResult]:
        """Validate multiple claims"""
        return [self.validate(text) for text in texts]
    
    def explain_rules(self) -> str:
        """Explain all rules in the system"""
        explanation = "SYMBOLIC REASONING RULES\n" + "=" * 50 + "\n\n"
        
        rules_explained = {
            'citation_exists': "Claim must have at least one citation",
            'citations_valid': "All citations must reference known statutes",
            'sufficient_citations': "Claim must have at least 2 citations",
            'legal_language': "Claim must use legal terminology",
            'proper_format': "Citations must be properly formatted",
            'citation_coherence': "Citations must commonly appear together",
            'minimum_length': "Claim must have at least 5 words",
            'not_gibberish': "Claim must be meaningful text",
            'logical_consistency': "Claim must not contain contradictions",
            'complete_claim': "Claim must be complete (10+ words, citations)",
        }
        
        for i, (rule, desc) in enumerate(rules_explained.items(), 1):
            explanation += f"{i}. {rule.replace('_', ' ').title()}:\n"
            explanation += f"   {desc}\n\n"
        
        return explanation

print("✅ Complete Symbolic System defined")

# ============================================================================
# PART 7: EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTING SYMBOLIC REASONING SYSTEM")
    print("=" * 70)
    
    # Create system (without corpus for demo)
    system = SymbolicReasoningSystem()
    
    # Test claims
    test_claims = [
        "The defendant violated Section 2 of the Contract Act as established in precedent",
        "This is random text with no legal meaning whatsoever",
        "The court ruled based on Section 10 and Article 5",
        "asdfghjkl random gibberish qwertyuiop",
        "The plaintiff's claim under the Property Act is well-founded"
    ]
    
    print("\n🔍 Testing claims...\n")
    
    for i, claim_text in enumerate(test_claims, 1):
        print(f"\nClaim {i}:")
        print(f"Text: '{claim_text}'")
        print("-" * 70)
        
        result = system.validate(claim_text)
        print(result.explanation)
        print(f"Confidence: {result.confidence:.1%}")
        print(f"Satisfied: {len(result.satisfied_rules)}/{len(system.rules_engine.rules)} rules")
    
    print("\n" + "=" * 70)
    print("✅ SYMBOLIC REASONING SYSTEM READY!")
    print("=" * 70)
    
    print("""
Next steps:
  1. Load your actual CSV data
  2. Combine with GNN predictions
  3. Build fusion network
""")