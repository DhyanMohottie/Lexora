import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:lexium_mobile/pages/login_page.dart';
import 'package:lexium_mobile/pages/settings_page.dart';
import 'package:lexium_mobile/pages/signup_page.dart';
import 'package:lexium_mobile/pages/chatbot_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);

  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      systemNavigationBarColor: Colors.transparent,
    ),
  );
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Lexium Mobile',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
      ),
      home: const LoginPage(),
      routes: {
        '/login': (context) => const LoginPage(),
        '/signup': (context) => const SignUpPage(),
        '/settings': (context) => const SettingsPage(),
        '/chatbot': (context) => const ChatBotPage(),
      },
      builder: (context, child) {
        return SafeArea(child: child!);
      },
    );
  }
}
