const express = require('express');
const router = express.Router();

// @desc    Get public configuration
// @route   GET /api/config/google
// @access  Public
router.get('/google', (req, res) => {
    res.json({
        success: true,
        data: {
            clientId: process.env.GOOGLE_CLIENT_ID
        }
    });
});

module.exports = router;
