import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lexium_mobile/providers/theme_provider.dart';
import 'package:lexium_mobile/services/auth_service.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  String? _email;
  String? _username;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchUserData();
  }

  Future<void> _fetchUserData() async {
    final result = await AuthService.getMe();

    if (!mounted) return;

    if (result['success']) {
      setState(() {
        _email = result['data']['user']['email'];
        _username = result['data']['user']['username'];
        _isLoading = false;
      });
    } else {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      resizeToAvoidBottomInset: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              child: Padding(
                padding: EdgeInsetsGeometry.symmetric(horizontal: 8.0),
                child: Column(
                  mainAxisSize: MainAxisSize.max,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 20),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16.0),
                      child: Text(
                        'My Profile',
                        style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.onSurface),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Card(
                      child: Column(
                        children: [
                          ListTile(
                            leading: Icon(Icons.person),
                            title: Text('Username'),
                            subtitle: Text(_username ?? 'N/A'),
                            trailing: Icon(Icons.chevron_right),
                          ),
                          Divider(
                              color:
                                  Theme.of(context).colorScheme.outlineVariant,
                              thickness: 1),
                          ListTile(
                            leading: Icon(Icons.email),
                            title: Text('Email'),
                            subtitle: Text(_email ?? 'N/A'),
                            trailing: Icon(Icons.chevron_right),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16.0),
                      child: Text(
                        'Account Settings',
                        style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.onSurface),
                      ),
                    ),
                    const SizedBox(height: 10),
                    const Card(
                      child: Column(
                        children: [
                          ListTile(
                            leading: Icon(Icons.manage_accounts),
                            title: Text('Manage Account'),
                            trailing: Icon(Icons.chevron_right),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16.0),
                      child: Text(
                        'Preferences',
                        style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.onSurface),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Card(
                      child: Column(
                        children: [
                          ListTile(
                            leading: Icon(Icons.notifications_none),
                            title: Text('Notifications'),
                            trailing: Icon(Icons.chevron_right),
                          ),
                          Divider(
                              color:
                                  Theme.of(context).colorScheme.outlineVariant,
                              thickness: 1),
                          Consumer<ThemeProvider>(
                            builder: (context, themeProvider, _) {
                              return ListTile(
                                leading: Icon(
                                  themeProvider.isDark
                                      ? Icons.dark_mode
                                      : Icons.light_mode,
                                ),
                                title: const Text('Appearance'),
                                trailing: Switch(
                                  value: themeProvider.isDark,
                                  onChanged: (_) => themeProvider.toggleTheme(),
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 40),
                    ElevatedButton(
                      onPressed: () {
                        Navigator.pushReplacementNamed(context, '/login');
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                        minimumSize: Size(double.infinity, 50),
                      ),
                      child: Text("Sign Out"),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
