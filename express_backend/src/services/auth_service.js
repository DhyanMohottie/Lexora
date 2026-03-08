const jwt = require('jsonwebtoken');
const User = require('../models/User');

// ─── Generate JWT Token ────────────────────────────────────────────────────
const generateToken = (id) => {
  return jwt.sign({ id }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  });
};

// ─── Create a new user ────────────────────────────────────────────────────
const createUser = async (email, password) => {
  const existingUser = await User.findOne({ email });
  if (existingUser) {
    const error = new Error('Email already in use');
    error.statusCode = 409;
    throw error;
  }

  const user = await User.create({ email, password });
  const token = generateToken(user._id);

  return {
    token,
    user: { id: user._id, email: user.email },
  };
};

// ─── Validate credentials and log in ──────────────────────────────────────
const loginUser = async (email, password) => {
  const user = await User.findOne({ email });
  if (!user || !(await user.comparePassword(password))) {
    const error = new Error('Invalid email or password');
    error.statusCode = 401;
    throw error;
  }

  const token = generateToken(user._id);

  return {
    token,
    user: { id: user._id, email: user.email },
  };
};

module.exports = { createUser, loginUser };