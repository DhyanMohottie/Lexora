const jwt = require('jsonwebtoken');
const User = require('../models/user');

//Generate JWT Token
const generateToken = (id) => {
  return jwt.sign({ id }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  });
};

//Create a new user
const createUser = async (email, password, username) => {
  const existingUser = await User.findOne({ email });
  if (existingUser) {
    const error = new Error('Email already in use');
    error.statusCode = 409;
    throw error;
  }

  const user = await User.create({ email, password, username });
  const token = generateToken(user._id);

  return {
    token,
    user: { id: user._id, email: user.email, username: user.username },
  };
};

//Validate credentials and log in
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
    user: { id: user._id, email: user.email, username: user.username },
  };
};

//Update Email
const updateEmail = async (userId, currentPassword, newEmail) => {
  const user = await User.findById(userId);
  if (!user || !(await user.comparePassword(currentPassword))) {
    const error = new Error('Current password is incorrect');
    error.statusCode = 401;
    throw error;
  }

  const existingUser = await User.findOne({ email: newEmail });
  if (existingUser) {
    const error = new Error('Email already in use');
    error.statusCode = 409;
    throw error;
  }

  user.email = newEmail;
  await user.save();

  return { user: { id: user._id, email: user.email, username: user.username } };
};

//Update Username
const updateUsername = async (userId, currentPassword, newUsername) => {
  const user = await User.findById(userId);
  if (!user || !(await user.comparePassword(currentPassword))) {
    const error = new Error('Current password is incorrect');
    error.statusCode = 401;
    throw error;
  }

  user.username = newUsername;
  await user.save();

  return { user: { id: user._id, email: user.email, username: user.username } };
};
//Update Password
const updatePassword = async (userId, currentPassword, newPassword) => {
  const user = await User.findById(userId);
  if (!user || !(await user.comparePassword(currentPassword))) {
    const error = new Error('Current password is incorrect');
    error.statusCode = 401;
    throw error;
  }

  user.password = newPassword;
  await user.save();

  return { message: 'Password updated successfully' };
};

module.exports = { createUser, loginUser, updateEmail, updateUsername, updatePassword };