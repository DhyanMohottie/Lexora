const express = require('express');
const router = express.Router();
const {
  signup,
  login,
  getMe,
  updateEmailHandler,
  updateUsernameHandler,
  updatePasswordHandler,
} = require('../controllers/auth_controller');
const { protect } = require('../middleware/auth_middleware');

router.post('/signup', signup);
router.post('/login', login);
router.get('/me', protect, getMe);
router.put('/update-email', protect, updateEmailHandler);
router.put('/update-username', protect, updateUsernameHandler);
router.put('/update-password', protect, updatePasswordHandler);

module.exports = router;