import 'package:flutter/material.dart';
import 'package:lexium_mobile/services/auth_service.dart';

class ManageAccountPage extends StatefulWidget {
  const ManageAccountPage({super.key});

  @override
  State<ManageAccountPage> createState() => _ManageAccountPageState();
}

class _ManageAccountPageState extends State<ManageAccountPage> {
  // ─── Show Edit Dialog ──────────────────────────────────────────────────────
  void _showEditDialog({
    required String title,
    required String newValueLabel,
    required String newValueHint,
    required TextInputType keyboardType,
    required Future<Map<String, dynamic>> Function(
            String currentPassword, String newValue)
        onSave,
    bool isPassword = false,
  }) {
    final currentPasswordController = TextEditingController();
    final newValueController = TextEditingController();
    final formKey = GlobalKey<FormState>();
    bool isLoading = false;
    bool isCurrentPasswordHidden = true;
    bool isNewValueHidden = true;
    String? errorMessage;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: Text(title),
              content: Form(
                key: formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // ── Error message ────────────────────────────────────
                    if (errorMessage != null)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.errorContainer,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color: Theme.of(context).colorScheme.error),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.error_outline,
                                color: Theme.of(context)
                                    .colorScheme
                                    .onErrorContainer,
                                size: 18),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                errorMessage!,
                                style: TextStyle(
                                  color: Theme.of(context)
                                      .colorScheme
                                      .onErrorContainer,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),

                    // ── Current Password ─────────────────────────────────
                    TextFormField(
                      controller: currentPasswordController,
                      obscureText: isCurrentPasswordHidden,
                      onChanged: (_) =>
                          setDialogState(() => errorMessage = null),
                      decoration: InputDecoration(
                        labelText: 'Current Password',
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(
                          icon: Icon(isCurrentPasswordHidden
                              ? Icons.visibility
                              : Icons.visibility_off),
                          onPressed: () => setDialogState(() =>
                              isCurrentPasswordHidden =
                                  !isCurrentPasswordHidden),
                        ),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Current password is required';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // ── New Value ────────────────────────────────────────
                    TextFormField(
                      controller: newValueController,
                      keyboardType: keyboardType,
                      obscureText: isPassword && isNewValueHidden,
                      onChanged: (_) =>
                          setDialogState(() => errorMessage = null),
                      decoration: InputDecoration(
                        labelText: newValueLabel,
                        hintText: newValueHint,
                        border: const OutlineInputBorder(),
                        suffixIcon: isPassword
                            ? IconButton(
                                icon: Icon(isNewValueHidden
                                    ? Icons.visibility
                                    : Icons.visibility_off),
                                onPressed: () => setDialogState(
                                    () => isNewValueHidden = !isNewValueHidden),
                              )
                            : null,
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return '$newValueLabel is required';
                        }
                        if (isPassword && value.length < 6) {
                          return 'Minimum 6 characters';
                        }
                        return null;
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                // ── Cancel ────────────────────────────────────────────────
                TextButton(
                  onPressed:
                      isLoading ? null : () => Navigator.pop(dialogContext),
                  child: const Text('Cancel'),
                ),
                // ── Save ──────────────────────────────────────────────────
                ElevatedButton(
                  onPressed: isLoading
                      ? null
                      : () async {
                          if (!formKey.currentState!.validate()) return;
                          setDialogState(() => isLoading = true);

                          final result = await onSave(
                            currentPasswordController.text,
                            newValueController.text.trim(),
                          );

                          if (!dialogContext.mounted) return;

                          if (result['success']) {
                            Navigator.pop(dialogContext);
                            if (!mounted) return;
                          } else {
                            setDialogState(() {
                              isLoading = false;
                              errorMessage = result['message'];
                            });
                          }
                        },
                  child: isLoading
                      ? const SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Account'),
        centerTitle: true,
      ),
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const SizedBox(height: 10),
            Card(
              child: Column(
                children: [
                  // ── Edit Email ───────────────────────────────────────────
                  ListTile(
                    leading: const Icon(Icons.email_outlined),
                    title: const Text('Edit Email'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _showEditDialog(
                      title: 'Edit Email',
                      newValueLabel: 'New Email',
                      newValueHint: 'Enter new email',
                      keyboardType: TextInputType.emailAddress,
                      onSave: (currentPassword, newEmail) =>
                          AuthService.updateEmail(
                        currentPassword: currentPassword,
                        newEmail: newEmail,
                      ),
                    ),
                  ),
                  Divider(
                    color: Theme.of(context).colorScheme.outlineVariant,
                    thickness: 1,
                  ),
                  // ── Edit Username ────────────────────────────────────────
                  ListTile(
                    leading: const Icon(Icons.person_outline),
                    title: const Text('Edit Username'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _showEditDialog(
                      title: 'Edit Username',
                      newValueLabel: 'New Username',
                      newValueHint: 'Enter new username',
                      keyboardType: TextInputType.text,
                      onSave: (currentPassword, newUsername) =>
                          AuthService.updateUsername(
                        currentPassword: currentPassword,
                        newUsername: newUsername,
                      ),
                    ),
                  ),
                  Divider(
                    color: Theme.of(context).colorScheme.outlineVariant,
                    thickness: 1,
                  ),

                  ListTile(
                    leading: const Icon(Icons.lock_outline),
                    title: const Text('Change Password'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _showEditDialog(
                      title: 'Change Password',
                      newValueLabel: 'New Password',
                      newValueHint: 'Enter new password',
                      keyboardType: TextInputType.visiblePassword,
                      isPassword: true,
                      onSave: (currentPassword, newPassword) =>
                          AuthService.updatePassword(
                        currentPassword: currentPassword,
                        newPassword: newPassword,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
