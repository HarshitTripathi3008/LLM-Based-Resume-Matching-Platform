const Resume = require('../models/Resume');
const path = require('path');
const axios = require('axios');
const fs = require('fs');



// AI Service URL (For production, set in Env)
let AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';
if (AI_SERVICE_URL.endsWith('/')) {
    AI_SERVICE_URL = AI_SERVICE_URL.slice(0, -1);
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
        const filePath = req.file.location || req.file.path; // S3 location or local path

        let resume = await Resume.create({
            user: req.user.id,
            fileName: req.file.key || req.file.filename, // S3 key or local filename
            filePath: filePath,
            originalName: req.file.originalname,
            mimeType: req.file.mimetype,
            status: 'processing'
        });

        // 2. Call Python Service
        try {
            let processingUrl = filePath;

            // If using S3, generate a signed URL for variables
            if (req.file.key) {
                const { GetObjectCommand } = require('@aws-sdk/client-s3');
                const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
                const s3 = require('../config/s3Config');

                const command = new GetObjectCommand({
                    Bucket: process.env.AWS_BUCKET_NAME,
                    Key: req.file.key,
                });

                // Url valid for 5 minutes
                processingUrl = await getSignedUrl(s3, command, { expiresIn: 300 });
            }

            const aiResponse = await axios.post(`${AI_SERVICE_URL}/process-resume`, {
                file_path: processingUrl
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
            if (aiError.response) {
                console.error("AI Response Data:", aiError.response.data);
            }
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

// @desc    Delete resume
// @route   DELETE /api/resumes/:id
// @access  Private
exports.deleteResume = async (req, res) => {
    try {
        const resume = await Resume.findById(req.params.id);

        if (!resume) {
            return res.status(404).json({ success: false, error: 'Resume not found' });
        }

        // Ensure user owns the resume
        if (resume.user.toString() !== req.user.id && req.user.role !== 'admin') {
            return res.status(401).json({ success: false, error: 'Not authorized' });
        }

        // Delete from S3
        const { DeleteObjectCommand } = require('@aws-sdk/client-s3');
        const s3 = require('../config/s3Config');

        // Extract Key from fileName or filePath (assuming fileName stored is the key or part of it)
        // In uploadResume we saved: fileName: req.file.key || req.file.filename
        // S3 Multer usually stores the key in req.file.key
        if (resume.fileName) {
            try {
                const deleteParams = {
                    Bucket: process.env.AWS_BUCKET_NAME,
                    Key: resume.fileName
                };
                await s3.send(new DeleteObjectCommand(deleteParams));
            } catch (s3Error) {
                console.error("S3 Delete Error:", s3Error);
                // Continue to delete from DB even if S3 fails? 
                // Usually yes, or user can't ever delete the record.
            }
        }

        await resume.deleteOne();

        res.status(200).json({ success: true, data: {}, message: 'Resume deleted successfully' });

    } catch (error) {
        console.error(error);
        res.status(500).json({ success: false, error: 'Server Error' });
    }
};
