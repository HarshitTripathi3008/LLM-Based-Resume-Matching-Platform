require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const app = express();

// Middleware
// 1. CORS MUST BE FIRST for Cloud/Lambda preflights
const allowedOrigins = [
    'http://resume-match-v2-web-937566678613.s3-website.eu-north-1.amazonaws.com',
    'https://resume-platform-frontend.onrender.com',
    'https://llm-based-resume-matching-platform.onrender.com',
    'http://127.0.0.1:5500',
    'http://127.0.0.1:5501',
    'http://localhost:5500',
    'http://localhost:5501',
    'http://localhost:3000'
];

app.use(cors({
    origin: function (origin, callback) {
        if (!origin || allowedOrigins.indexOf(origin) !== -1) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

// 2. Body Parser
app.use(express.json());

// Relax Helmet for Google OAuth
app.use(helmet({
    crossOriginOpenerPolicy: { policy: "same-origin-allow-popups" },
    crossOriginResourcePolicy: { policy: "cross-origin" }
}));

app.use(morgan('dev'));

// Basic Route
app.get('/', (req, res) => {
    res.json({ message: 'API is running...' });
});

// Routes
const authRoutes = require('./routes/authRoutes');
const resumeRoutes = require('./routes/resumeRoutes');
const jobRoutes = require('./routes/jobRoutes');
const configRoutes = require('./routes/configRoutes');

app.use('/api/auth', authRoutes);
app.use('/api/resumes', resumeRoutes);
app.use('/api/jobs', jobRoutes);
app.use('/api/config', configRoutes);

module.exports = app;
