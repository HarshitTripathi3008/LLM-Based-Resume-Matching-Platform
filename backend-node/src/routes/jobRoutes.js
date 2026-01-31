const express = require('express');
const { createJob, getJobs, matchCandidates, getRecommendedJobs } = require('../controllers/jobController');
const { protect } = require('../middlewares/authMiddleware');

const router = express.Router();

// Public route to view jobs? Or protected? Let's make view public, create protected.
router.get('/', getJobs);
router.post('/', protect, createJob);
router.get('/:id/match', protect, matchCandidates);
router.post('/recommend', protect, getRecommendedJobs);

module.exports = router;
