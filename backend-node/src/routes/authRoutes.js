const express = require('express');
const { googleLogin, getMe } = require('../controllers/authController');
const { protect } = require('../middlewares/authMiddleware');

const router = express.Router();

router.post('/google', googleLogin);
router.get('/me', protect, getMe);

module.exports = router;
