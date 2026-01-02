import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:lexium_mobile/widgets/signup_form.dart';

class SignUpPage extends StatefulWidget {
  const SignUpPage({super.key});

  @override
  State<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends State<SignUpPage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Account'), centerTitle: true),
      resizeToAvoidBottomInset: true,
      backgroundColor: Colors.grey[200],
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: Column(
            mainAxisSize: MainAxisSize.max,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(width: double.infinity),
              const SizedBox(height: 20),
              const Text(
                'Get Started',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
               const SizedBox(height: 10),
              const Text(
                'Create an Account to Access legal information.',
                style: TextStyle(fontSize: 14),
              ),
              const SizedBox(height: 20),
              const SignupForm(),
            ],
          ),
        ),
      ),
    );
  }
}
