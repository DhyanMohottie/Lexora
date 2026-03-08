const { createUser, loginUser } = require('../services/auth_service');

// @route   POST /api/auth/signup
const signup = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required' });
    }

    const data = await createUser(email, password);

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
    },
  });
};

module.exports = { signup, login, getMe };