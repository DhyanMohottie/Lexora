class Confidence {
  final double fusedScore;
  final double gnnScore;
  final double symbolicConfidence;
  final int rulesSatisfied;
  final int rulesViolated;
  final bool isValid;

  Confidence({
    required this.fusedScore,
    required this.gnnScore,
    required this.symbolicConfidence,
    required this.rulesSatisfied,
    required this.rulesViolated,
    required this.isValid,
  });

  factory Confidence.fromJson(Map<String, dynamic> json) => Confidence(
    fusedScore: (json['fused_score'] ?? 0).toDouble(),
    gnnScore: (json['gnn_score'] ?? 0).toDouble(),
    symbolicConfidence: (json['symbolic_confidence'] ?? 0).toDouble(),
    rulesSatisfied: json['rules_satisfied'] ?? 0,
    rulesViolated: json['rules_violated'] ?? 0,
    isValid: json['is_valid'] ?? false,
  );
}

class ChatResponse {
  final String answer;
  final String initialAnswer;
  final Confidence confidence;
  final Confidence initialConfidence;
  final bool wasCorrected;
  final int correctionsMade;

  ChatResponse({
    required this.answer,
    required this.initialAnswer,
    required this.confidence,
    required this.initialConfidence,
    required this.wasCorrected,
    required this.correctionsMade,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) => ChatResponse(
    answer: json['answer'] ?? '',
    initialAnswer: json['initial_answer'] ?? '',
    confidence: Confidence.fromJson(json['confidence'] ?? {}),
    initialConfidence: Confidence.fromJson(json['initial_confidence'] ?? {}),
    wasCorrected: json['was_corrected'] ?? false,
    correctionsMade: json['corrections_made'] ?? 0,
  );
}

class ChatMessage {
  final String text;
  final bool isUser;
  final Confidence? confidence;
  final bool wasCorrected;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.confidence,
    this.wasCorrected = false,
  });
}