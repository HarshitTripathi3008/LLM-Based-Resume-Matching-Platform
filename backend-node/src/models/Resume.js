const mongoose = require('mongoose');

const resumeSchema = new mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    fileName: {
        type: String,
        required: true
    },
    filePath: {
        type: String, // Local path or S3 URL
        required: true
    },
    originalName: {
        type: String,
        required: true
    },
    mimeType: {
        type: String,
        required: true
    },
    // Extracted Data (Empty initially, populated by AI service)
    parsedData: {
        skills: [String],
        experience: [{
            title: String,
            company: String,
            years: Number
        }],
        education: [{
            degree: String,
            school: String,
            year: String
        }],
        summary: String
    },
    // Raw text content for indexing
    rawText: {
        type: String
    },
    status: {
        type: String,
        enum: ['uploaded', 'processing', 'completed', 'failed'],
        default: 'uploaded'
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Resume', resumeSchema);
