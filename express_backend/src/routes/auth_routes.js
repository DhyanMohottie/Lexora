const express = require('express');
const router = express.Router();
const { signup, login, getMe } = require('../controllers/auth_controller');
const { protect } = require('../middleware/auth_middleware');

router.post('/signup', signup);
router.post('/login', login);
router.get('/me', protect, getMe);

module.exports = router;