import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // For emulator use 10.0.2.2, for real device use your PC's IP
  static const String baseUrl = 'http://1.208.108.242:58437';
  // static const String baseUrl = 'http://192.168.8.169:5000';

  static Future<Map<String, dynamic>> sendMessage(
    String question, {
    List<Map<String, String>> history = const [],
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'question': question,
        'conversation_history': history,
      }),
    ).timeout(const Duration(seconds: 120));

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Server error: ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> validateClaim(String claim) async {
    final response = await http.post(
      Uri.parse('$baseUrl/validate'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'claim': claim}),
    ).timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Server error: ${response.statusCode}');
    }
  }

  static Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
      ).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}