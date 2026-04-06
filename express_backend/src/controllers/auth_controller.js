const { createUser, loginUser, updateEmail, updateUsername, updatePassword } = require('../services/auth_service');

// @route   POST /api/auth/signup
const signup = async (req, res) => {
  try {
    const { email, password, username } = req.body;

    if (!email || !password || !username) {
      return res.status(400).json({ message: 'Email, username, and password are required' });
    }

    const data = await createUser(email, password, username);

    res.status(201).json({
      message: 'Account created successfully',
      ...data,
    });
  } catch (error) {
    res.status(error.statusCode || 500).json({ message: error.message });
  }
};

// @route   POST /api/auth/login
const login = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required' });
    }

    const data = await loginUser(email, password);

    res.status(200).json({
      message: 'Login successful',
      ...data,
    });
  } catch (error) {
    res.status(error.statusCode || 500).json({ message: error.message });
  }
};

// @route   GET /api/auth/me  (protected)
const getMe = async (req, res) => {
  res.status(200).json({
    user: {
      id: req.user._id,
      email: req.user.email,
      username: req.user.username,
    },
  });
};

// @route   PUT /api/auth/update-email  (protected)
const updateEmailHandler = async (req, res) => {
  try {
    const { currentPassword, newEmail } = req.body;
 
    if (!currentPassword || !newEmail) {
      return res.status(400).json({ message: 'Current password and new email are required' });
    }
 
    const data = await updateEmail(req.user._id, currentPassword, newEmail);
    res.status(200).json({ message: 'Email updated successfully', ...data });
  } catch (error) {
    res.status(error.statusCode || 500).json({ message: error.message });
  }
};
 
// @route   PUT /api/auth/update-username  (protected)
const updateUsernameHandler = async (req, res) => {
  try {
    const { currentPassword, newUsername } = req.body;
 
    if (!currentPassword || !newUsername) {
      return res.status(400).json({ message: 'Current password and new username are required' });
    }
 
    const data = await updateUsername(req.user._id, currentPassword, newUsername);
    res.status(200).json({ message: 'Username updated successfully', ...data });
  } catch (error) {
    res.status(error.statusCode || 500).json({ message: error.message });
  }
};
 
// @route   PUT /api/auth/update-password  (protected)
const updatePasswordHandler = async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;
 
    if (!currentPassword || !newPassword) {
      return res.status(400).json({ message: 'Current password and new password are required' });
    }
 
    if (newPassword.length < 6) {
      return res.status(400).json({ message: 'New password must be at least 6 characters' });
    }
 
    const data = await updatePassword(req.user._id, currentPassword, newPassword);
    res.status(200).json(data);
  } catch (error) {
    res.status(error.statusCode || 500).json({ message: error.message });
  }
};
 
module.exports = { signup, login, getMe, updateEmailHandler, updateUsernameHandler, updatePasswordHandler };