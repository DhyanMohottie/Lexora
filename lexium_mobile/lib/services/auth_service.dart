import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AuthService {
  // Change this to your machine's IP when testing on a real device
  // Use 10.0.2.2 for Android emulator, localhost for iOS simulator
  static const String baseUrl = 'http://192.168.1.6:3000/api';

  // ─── Sign Up ───────────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> signup({
    required String email,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 201) {
        await _saveToken(data['token']);
        return {'success': true, 'data': data};
      } else {
        return {'success': false, 'message': data['message']};
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'Network error. Check your connection.'
      };
    }
  }

  // ─── Login ─────────────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/auth/login'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email, 'password': password}),
          )
          .timeout(
            const Duration(seconds: 10),
            onTimeout: () => throw Exception('Request timed out'),
          );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        await _saveToken(data['token']);
        return {'success': true, 'data': data};
      } else {
        return {'success': false, 'message': data['message']};
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'Network error. Check your connection.'
      };
    }
  }

  // ─── Logout ────────────────────────────────────────────────────────────────
  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
  }

  // ─── Get saved token ───────────────────────────────────────────────────────
  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  // ─── Check if logged in ────────────────────────────────────────────────────
  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
  }

  // ─── Private: save token ───────────────────────────────────────────────────
  static Future<void> _saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }
}
