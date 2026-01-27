const Job = require('../models/Job');
const Resume = require('../models/Resume');
const axios = require('axios');

// AI Service URL
let AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';
if (!AI_SERVICE_URL.startsWith('http')) {
    AI_SERVICE_URL = `http://${AI_SERVICE_URL}`;
}

// @desc    Create a new job (Manual or Scraped)
// @route   POST /api/jobs
// @access  Private (Employer/Admin)
exports.createJob = async (req, res) => {
    try {
        let { title, company, description, url } = req.body;

        // If URL provided, try to scrape
        if (url && !description) {
            try {
                // Call Python Service
                const response = await axios.post(`${AI_SERVICE_URL}/scrape-job`, { url });
                if (response.data.success) {
                    description = response.data.data;
                }
            } catch (err) {
                console.error("AI Service Error (Scraping):", err.message);
                // Continue without description or return error?
                // For now, allow continuing if user provided title
            }
        }

        const job = await Job.create({
            user: req.user.id,
            title,
            company,
            description,
            sourceUrl: url
        });

        res.status(201).json({
            success: true,
            data: job
        });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
};

// @desc    Get all jobs
// @route   GET /api/jobs
// @access  Public
exports.getJobs = async (req, res) => {
    try {
        const jobs = await Job.find().sort({ createdAt: -1 });
        res.status(200).json({ success: true, count: jobs.length, data: jobs });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
};

// @desc    Match candidates to a job
// @route   GET /api/jobs/:id/match
// @access  Private
exports.matchCandidates = async (req, res) => {
    try {
        const job = await Job.findById(req.params.id);
        if (!job) {
            return res.status(404).json({ success: false, error: 'Job not found' });
        }

        // Get all resumes (In prod, filter by active)
        const resumes = await Resume.find();

        const matchedResumes = [];

        for (const resume of resumes) {
            // Need extracted text. If not in DB, we skip (or handle async)
            // Ideally Resume model should have 'analyzedText' or we use rawText.
            // For now, let's assume raw text is stored or we re-extract (expensive).
            // Let's use 'rawText' field we added to Resume model.

            // NOTE: In Phase 2 we didn't populate rawText yet.
            // Assumption: Resume has text.

            if (resume.rawText || resume.parsedData) {
                // Prepare text representation
                const resumeText = resume.rawText || JSON.stringify(resume.parsedData);

                try {
                    const response = await axios.post(`${AI_SERVICE_URL}/match-jobs`, {
                        resume_text: resumeText,
                        job_description: job.description
                    });

                    if (response.data.success) {
                        matchedResumes.push({
                            resume,
                            score: response.data.data.match_percentage,
                            missing_keywords: response.data.data.missing_keywords
                        });
                    }
                } catch (err) {
                    console.error("Matching Error", err.message);
                }
            }
        }

        // Sort by Score
        matchedResumes.sort((a, b) => b.score - a.score);

        res.status(200).json({
            success: true,
            job_title: job.title,
            candidates: matchedResumes
        });

    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
};
