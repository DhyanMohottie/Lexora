import 'package:flutter/material.dart';

class SignupForm extends StatefulWidget {
  const SignupForm({super.key});

  @override
  State<SignupForm> createState() => _SignupFormState();
}

class _SignupFormState extends State<SignupForm> {
  bool _isPasswordHidden = true;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        const Align(
          alignment: Alignment.centerLeft,
          child: Text(
            'Email Address:',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ),
        const SizedBox(height: 8),
        const TextField(
          decoration: InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'Enter your Email',
          ),
        ),
        const SizedBox(height: 20),
        const Align(
          alignment: Alignment.centerLeft,
          child: Text(
            'Password:',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          obscureText: _isPasswordHidden,
          decoration: InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'Enter your Password',
            suffixIcon: IconButton(
              icon: Icon(
                _isPasswordHidden ? Icons.visibility : Icons.visibility_off,
              ),
              onPressed: () {
                setState(() {
                  _isPasswordHidden = !_isPasswordHidden;
                });
              },
            ),
          ),
        ),
        const SizedBox(height: 20),
        const Align(
          alignment: Alignment.centerLeft,
          child: Text(
            'Confirm Password:',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          obscureText: _isPasswordHidden,
          decoration: InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'Confirm your Password',
            suffixIcon: IconButton(
              icon: Icon(
                _isPasswordHidden ? Icons.visibility : Icons.visibility_off,
              ),
              onPressed: () {
                setState(() {
                  _isPasswordHidden = !_isPasswordHidden;
                });
              },
            ),
          ),
        ),
        const SizedBox(height: 150),
        ElevatedButton(
          onPressed: () {
            Navigator.pushNamedAndRemoveUntil(
              context,
              '/chatbot',
              (route) => false,
            );
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: Theme.of(context).colorScheme.primary,
            foregroundColor: Theme.of(context).colorScheme.onPrimary,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8.0),
            ),
            minimumSize: Size(double.infinity, 50),
          ),

          child: Text("Create Account"),
        ),
        const SizedBox(height: 16),
      ],
    );
  }
}
