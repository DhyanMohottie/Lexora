"""
Neurosymbolic Legal AI - Flask API
===================================
Lives inside lexium_mobile_backend/ alongside your existing files.

Imports directly from:
    - gnn_model.py              (your existing GNN)
    - symbolic_reasoning_system.py  (your existing Symbolic engine)
    - fusion_network.py          (your existing Fusion network)

New files added:
    - app.py                     (this file - Flask API)
    - llm_service.py             (LLM integration)
    - self_correction.py         (iterative correction loop)

Folder structure:
    lexium_mobile_backend/
    ├── gnn_model.py                    ← EXISTING (don't touch)
    ├── symbolic_reasoning_system.py    ← EXISTING (don't touch)
    ├── fusion_network.py               ← EXISTING (don't touch)
    ├── app.py                          ← NEW (this file)
    ├── llm_service.py                  ← NEW
    ├── self_correction.py              ← NEW
    ├── .env                            ← NEW (create from .env.example)
    ├── requirements.txt                ← NEW
    ├── models/
    │   ├── legal_gnn_trained_no_cases.pt   ← EXISTING
    │   └── fusion_network.pt               ← EXISTING
    └── data/
        ├── statutes.csv                ← EXISTING
        ├── sections.csv                ← EXISTING
        └── documents.csv               ← EXISTING
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import json
import time
import traceback

# ── Import from YOUR EXISTING files ──────────────────────────────
from gnn_model import predict_claim
from symbolic_reasoning_system import validate_claim as symbolic_validate, get_system
from fusion_network import FusionPredictor
# ─────────────────────────────────────────────────────────────────

from llm_service import LegalLLMService
from self_correction import SelfCorrectionController

app = Flask(__name__)
CORS(app)

# ============================================
# STARTUP: Load all models
# ============================================
print("=" * 60)
print("NEUROSYMBOLIC LEGAL AI - Starting up...")
print("=" * 60)

# GNN loads automatically via gnn_model.py global predictor
print("Loading GNN Engine...")
try:
    _test = predict_claim("test claim")
    GNN_READY = True
    print("✅ GNN Engine ready")
except Exception as e:
    GNN_READY = False
    print(f"⚠️  GNN Engine failed: {e}")

# Symbolic loads automatically via symbolic_reasoning_system.py
print("Loading Symbolic Engine...")
try:
    _test = symbolic_validate("test claim")
    SYMBOLIC_READY = True
    print("✅ Symbolic Engine ready (10 rules)")
except Exception as e:
    SYMBOLIC_READY = False
    print(f"⚠️  Symbolic Engine failed: {e}")

# Fusion Network
print("Loading Fusion Network...")
try:
    fusion_path = os.getenv('FUSION_MODEL_PATH', 'models/fusion_network.pt')
    fusion_predictor = FusionPredictor(fusion_path)
    FUSION_READY = True
except Exception as e:
    fusion_predictor = None
    FUSION_READY = False
    print(f"⚠️  Fusion Network failed: {e}")

# LLM Service
llm_service = LegalLLMService(
    model_name=os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
    api_key=os.getenv('OPENAI_API_KEY', None)
)


# ============================================
# VALIDATION FUNCTION (uses your 3 existing modules)
# ============================================

def validate_with_neurosymbolic(claim_text: str) -> dict:
    """
    Run full validation pipeline using your existing modules.
    
    GNN (gnn_model.py) → gnn_score
    Symbolic (symbolic_reasoning_system.py) → confidence, rules
    Fusion (fusion_network.py) → fused_score
    """
    # 1. GNN
    try:
        gnn_result = predict_claim(claim_text)
        gnn_score = gnn_result['gnn_score']
    except Exception as e:
        print(f"⚠️ GNN error: {e}")
        gnn_score = 0.5

    # 2. Symbolic
    try:
        symbolic_result = symbolic_validate(claim_text)
        symbolic_confidence = symbolic_result.confidence
        satisfied_rules = symbolic_result.satisfied_rules
        violations = symbolic_result.violations
        is_valid = symbolic_result.is_valid
        explanation = symbolic_result.explanation
    except Exception as e:
        print(f"⚠️ Symbolic error: {e}")
        symbolic_confidence = 0.5
        satisfied_rules = []
        violations = []
        is_valid = False
        explanation = "Symbolic engine error"

    num_satisfied = len(satisfied_rules)
    num_violations = len(violations)

    # 3. Fusion
    if fusion_predictor is not None:
        try:
            fused_score = fusion_predictor.predict(
                gnn_score, symbolic_confidence, num_satisfied, num_violations
            )
        except Exception as e:
            print(f"⚠️ Fusion error: {e}")
            fused_score = 0.4 * gnn_score + 0.6 * symbolic_confidence
    else:
        # Weighted average fallback
        fused_score = 0.4 * gnn_score + 0.6 * symbolic_confidence

    return {
        'fused_score': round(fused_score, 4),
        'gnn_score': round(gnn_score, 4),
        'symbolic_confidence': round(symbolic_confidence, 4),
        'symbolic_is_valid': is_valid,
        'satisfied_rules': satisfied_rules,
        'violations': violations,
        'num_satisfied': num_satisfied,
        'num_violations': num_violations,
        'explanation': explanation
    }


# Self-Correction Controller
self_correction = SelfCorrectionController(
    validate_fn=validate_with_neurosymbolic,
    llm_service=llm_service,
    threshold=float(os.getenv('CORRECTION_THRESHOLD', '0.70')),
    max_retries=int(os.getenv('MAX_RETRIES', '3'))
)

print("=" * 60)
print("✅ All systems ready!")
print(f"   GNN: {'✅' if GNN_READY else '❌'}")
print(f"   Symbolic: {'✅' if SYMBOLIC_READY else '❌'}")
print(f"   Fusion: {'✅' if FUSION_READY else '❌'}")
print(f"   LLM: {'✅' if llm_service.is_ready() else '❌'}")
print("=" * 60)


# ============================================
# ROUTES
# ============================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'components': {
            'gnn_engine': GNN_READY,
            'symbolic_engine': SYMBOLIC_READY,
            'fusion_network': FUSION_READY,
            'llm_service': llm_service.is_ready()
        },
        'config': {
            'threshold': self_correction.threshold,
            'max_retries': self_correction.max_retries
        },
        'timestamp': time.time()
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    Full neurosymbolic chat pipeline.
    
    Request:
        { "question": "What does Section 2 of the Contract Act say?",
          "conversation_history": [] }
    
    Response:
        { "initial_answer": "...", "initial_confidence": {...},
          "answer": "...", "confidence": {...},
          "was_corrected": true, "corrections_made": 2, "success": true }
    
    Flutter usage:
        1. Show initial_answer + initial_confidence immediately
        2. If was_corrected == true → replace with answer + confidence
    """
    try:
        data = request.json
        question = data.get('question', '').strip()
        history = data.get('conversation_history', [])

        if not question:
            return jsonify({'success': False, 'error': 'Question is required'}), 400

        result = self_correction.process(question, history)

        return jsonify({
            'initial_answer': result['initial_answer'],
            'initial_confidence': result['initial_confidence'],
            'answer': result['answer'],
            'confidence': result['confidence'],
            'was_corrected': result['was_corrected'],
            'corrections_made': result['corrections_made'],
            'success': True
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """
    SSE streaming version.
    Events: initial → correcting → final → done
    """
    try:
        data = request.json
        question = data.get('question', '').strip()
        history = data.get('conversation_history', [])

        if not question:
            return jsonify({'success': False, 'error': 'Question is required'}), 400

        def generate():
            try:
                # Phase 1: Initial answer
                initial_answer = llm_service.generate(question, history)
                initial_validation = validate_with_neurosymbolic(initial_answer)
                initial_score = initial_validation['fused_score']

                yield f"data: {json.dumps({'event': 'initial', 'answer': initial_answer, 'confidence': {'fused_score': initial_score, 'gnn_score': initial_validation['gnn_score'], 'symbolic_confidence': initial_validation['symbolic_confidence'], 'rules_satisfied': initial_validation['num_satisfied'], 'rules_violated': initial_validation['num_violations'], 'is_valid': initial_validation['symbolic_is_valid']}})}\n\n"

                # Phase 2: Check threshold
                threshold = self_correction.threshold
                if initial_score >= threshold:
                    yield f"data: {json.dumps({'event': 'done', 'was_corrected': False, 'corrections_made': 0})}\n\n"
                    return

                # Phase 3: Silent correction
                yield f"data: {json.dumps({'event': 'correcting', 'message': 'Improving answer quality...'})}\n\n"

                best_answer = initial_answer
                best_score = initial_score
                best_validation = initial_validation
                current_validation = initial_validation
                corrections = 0

                for attempt in range(1, self_correction.max_retries + 1):
                    corrections = attempt
                    try:
                        corrected = llm_service.generate_with_context(question, current_validation)
                        corrected_val = validate_with_neurosymbolic(corrected)
                        corrected_score = corrected_val['fused_score']

                        if corrected_score > best_score:
                            best_answer = corrected
                            best_score = corrected_score
                            best_validation = corrected_val

                        if corrected_score >= threshold:
                            break
                        current_validation = corrected_val
                    except Exception as e:
                        print(f"Correction {attempt} failed: {e}")
                        break

                # Phase 4: Send final
                was_corrected = best_answer != initial_answer
                if was_corrected:
                    yield f"data: {json.dumps({'event': 'final', 'answer': best_answer, 'confidence': {'fused_score': best_score, 'gnn_score': best_validation['gnn_score'], 'symbolic_confidence': best_validation['symbolic_confidence'], 'rules_satisfied': best_validation['num_satisfied'], 'rules_violated': best_validation['num_violations'], 'is_valid': best_validation['symbolic_is_valid']}, 'corrections_made': corrections})}\n\n"

                yield f"data: {json.dumps({'event': 'done', 'was_corrected': was_corrected, 'corrections_made': corrections})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/validate', methods=['POST'])
def validate():
    """Direct claim validation (no LLM)"""
    try:
        data = request.json
        claim = data.get('claim', '').strip()
        if not claim:
            return jsonify({'success': False, 'error': 'Claim text is required'}), 400

        result = validate_with_neurosymbolic(claim)
        return jsonify({
            'fused_score': result['fused_score'],
            'gnn_score': result['gnn_score'],
            'symbolic': {
                'confidence': result['symbolic_confidence'],
                'is_valid': result['symbolic_is_valid'],
                'satisfied_rules': result['satisfied_rules'],
                'violations': result['violations'],
                'explanation': result['explanation']
            },
            'success': True
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/validate/batch', methods=['POST'])
def validate_batch():
    """Validate multiple claims"""
    try:
        data = request.json
        claims = data.get('claims', [])
        if not claims:
            return jsonify({'success': False, 'error': 'Claims list is required'}), 400

        results = [validate_with_neurosymbolic(c) for c in claims]
        return jsonify({'results': results, 'count': len(results), 'success': True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# RUN
# ============================================
if __name__ == '__main__':
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )