const Resume = require('../models/Resume');
const path = require('path');
const axios = require('axios');
const fs = require('fs');

const axios = require('axios');
const fs = require('fs');

// AI Service URL (For production, set in Env)
let AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';
if (!AI_SERVICE_URL.startsWith('http')) {
    AI_SERVICE_URL = `http://${AI_SERVICE_URL}`;
}

// @desc    Upload a resume
// @route   POST /api/resumes/upload
// @access  Private
exports.uploadResume = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ success: false, error: 'Please upload a file' });
        }

        // 1. Create initial record
        let resume = await Resume.create({
            user: req.user.id,
            fileName: req.file.filename,
            filePath: req.file.path,
            originalName: req.file.originalname,
            mimeType: req.file.mimetype,
            status: 'processing'
        });

        // 2. Call Python Service
        // We need to send the ABSOLUTE path or ensuring Python can access it.
        // Since both are local, we can send the full path.
        const fullPath = path.resolve(req.file.path);

        try {
            const aiResponse = await axios.post(`${AI_SERVICE_URL}/process-resume`, {
                file_path: fullPath
            });

            if (aiResponse.data.success) {
                // 3. Update Resume with AI Data
                resume.rawText = aiResponse.data.text_preview; // Or full text if we change API
                // If API returns 'data' (JSON), save it
                if (aiResponse.data.data) {
                    resume.parsedData = aiResponse.data.data;
                }
                resume.status = 'completed';
                await resume.save();
            }
        } catch (aiError) {
            console.error("AI Processing Failed:", aiError.message);
            resume.status = 'failed';
            await resume.save();
            // We don't fail the request, just the processing status
        }

        res.status(201).json({
            success: true,
            data: resume,
            message: 'File uploaded and processed.'
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ success: false, error: 'Server Error during upload' });
    }
};

// @desc    Get all resumes for the logged in user
// @route   GET /api/resumes
// @access  Private
exports.getMyResumes = async (req, res) => {
    try {
        const resumes = await Resume.find({ user: req.user.id }).sort({ createdAt: -1 });
        res.status(200).json({
            success: true,
            count: resumes.length,
            data: resumes
        });
    } catch (error) {
        res.status(500).json({ success: false, error: 'Server Error' });
    }
};

// @desc    Get single resume by ID
// @route   GET /api/resumes/:id
// @access  Private
exports.getResumeById = async (req, res) => {
    try {
        const resume = await Resume.findById(req.params.id);

        if (!resume) {
            return res.status(404).json({ success: false, error: 'Resume not found' });
        }

        // Ensure user owns the resume (or is admin)
        if (resume.user.toString() !== req.user.id && req.user.role !== 'admin') {
            return res.status(401).json({ success: false, error: 'Not authorized' });
        }

        res.status(200).json({
            success: true,
            data: resume
        });
    } catch (error) {
        res.status(500).json({ success: false, error: 'Server Error' });
    }
};
