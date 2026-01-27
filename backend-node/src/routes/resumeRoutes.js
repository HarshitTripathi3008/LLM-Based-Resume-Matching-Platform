const express = require('express');
const { uploadResume, getMyResumes, getResumeById } = require('../controllers/resumeController');
const { protect } = require('../middlewares/authMiddleware');
const upload = require('../utils/fileUpload');

const router = express.Router();

// Apply auth middleware to all routes
router.use(protect);

router.post('/upload', upload.single('resume'), uploadResume);
router.get('/', getMyResumes);
router.get('/:id', getResumeById);

module.exports = router;
