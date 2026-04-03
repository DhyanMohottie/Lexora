import 'package:flutter/material.dart';
import 'package:lexium_mobile/services/auth_service.dart';

class SignupController {
  final BuildContext context;
  final GlobalKey<FormState> formKey;
  final TextEditingController emailController;
  final TextEditingController passwordController;
  final TextEditingController usernameController;
  final void Function(bool) setLoading;
  final void Function(String?) setError;

  SignupController({
    required this.context,
    required this.formKey,
    required this.emailController,
    required this.passwordController,
    required this.usernameController,
    required this.setLoading,
    required this.setError,
  });

  bool _isLoading = false;

  Future<void> handleSignup() async {

    if (_isLoading) return;

    setError(null);

    if (!formKey.currentState!.validate()) return;

    FocusScope.of(context).unfocus();

    _isLoading = true;
    setLoading(true);

    try {
      final result = await AuthService.signup(
        email: emailController.text.trim(),
        password: passwordController.text,
        username: usernameController.text.trim(),
      );

      _isLoading = false;
      if (!context.mounted) return;
      setLoading(false);

      if (result['success']) {
        Navigator.pushNamedAndRemoveUntil(
          context,
          '/chatbot',
          (route) => false,
        );
      } else {
        passwordController.clear();
        setError(result['message'] ?? 'Could not create account. Try again.');
      }
    } catch (e) {
      _isLoading = false;
      if (!context.mounted) return;
      setLoading(false);
      passwordController.clear();
      setError('Something went wrong. Please try again.');
    }
  }
}