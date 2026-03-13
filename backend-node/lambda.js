const serverless = require('serverless-http');
const app = require('./src/app');
const connectDB = require('./src/config/db');

// DB connection cache
let isConnected = false;

const handler = serverless(app, {
    async request(request, event, context) {
        if (!isConnected) {
            await connectDB();
            isConnected = true;
        }
    },
});

module.exports.handler = handler;
