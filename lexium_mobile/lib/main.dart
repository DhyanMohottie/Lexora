import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:lexium_mobile/pages/login_page.dart';
import 'package:lexium_mobile/pages/settings_page.dart';
import 'package:lexium_mobile/pages/signup_page.dart';
import 'package:lexium_mobile/pages/chatbot_page.dart';
import 'package:provider/provider.dart';
import 'package:lexium_mobile/providers/theme_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);

  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      systemNavigationBarColor: Colors.transparent,
    ),
  );
  runApp(
    ChangeNotifierProvider(
      create: (_) => ThemeProvider(),
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const AppRoot();
  }
}

class AppRoot extends StatelessWidget {
  const AppRoot({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Lexium Mobile',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          brightness: Brightness.dark,
        ),
      ),
      themeMode: themeProvider.themeMode,
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
