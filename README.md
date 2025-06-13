# Document Upload & AI Analysis Platform

A full-stack web application built as a technical demonstration that allows users to upload documents (PDF/TXT) and analyze them using Google's Gemini AI with customizable prompt templates. This project showcases real-time processing, AI integration, and modern web development practices.

**🎯 Project Overview**: This is a complete implementation of a document analysis platform featuring real-time upload progress, AI-powered document analysis with Google Gemini, and a modern React frontend with prompt testing capabilities.

## 🚀 Features

### Core Functionality
- **File Upload**: Drag-and-drop interface for PDF and TXT files (max 5MB)
- **Real-time Processing**: Server-sent events (SSE) for live upload and processing status
- **AI Analysis**: Document analysis using Google Gemini API with custom prompts
- **Prompt Templates**: Pre-built and custom prompt templates for different analysis types
- **Results Management**: View, copy, and export analysis results

### AI Analysis Features
- Document summarization
- Key points extraction  
- Sentiment analysis
- Custom question answering
- Entity extraction (people, dates, amounts)

### Technical Features
- **Backend**: FastAPI with async/await, PostgreSQL, Redis caching
- **Frontend**: React with Tailwind CSS, real-time updates via SSE
- **Real-time Updates**: Server-sent events for live progress tracking
- **Rate Limiting**: API rate limiting (10 requests/minute) to prevent abuse
- **Document Processing**: Multi-stage pipeline with status tracking
- **AI Integration**: Gemini Pro API with retry logic and error handling
- **Response Caching**: Redis caching for identical prompt+document pairs
- **Responsive Design**: Mobile-friendly interface

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   React         │◄──►│   FastAPI       │◄──►│   PostgreSQL    │
│   Frontend      │    │   Backend       │    │   Database      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │                 │    │                 │
                    │   Redis         │    │   Gemini AI     │
                    │   Cache         │    │   API           │
                    │                 │    │                 │
                    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Docker and Docker Compose
- Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
- Git

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-Analysis-And-Testing-Platform
   ```

2. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your Gemini API key
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your-super-secret-key-here
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

5. **Initialize default templates** (Optional)
   - The system comes with pre-built prompt templates
   - Access them via the Templates page in the UI

## 🗄️ Database Schema

The application uses three main tables as specified in the requirements:

### Documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    upload_time TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'uploaded',
    current_stage VARCHAR(500),
    progress INTEGER DEFAULT 0,
    extracted_text TEXT,
    text_length INTEGER,
    language VARCHAR(10)
);
```

### Prompt Templates
```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    category VARCHAR(50), -- 'summary', 'analysis', 'extraction', 'custom'
    variables JSONB, -- [{name: 'document_content', required: true}]
    example_output TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    is_public BOOLEAN DEFAULT TRUE
);
```

### AI Analyses
```sql
CREATE TABLE ai_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    prompt_template_id UUID REFERENCES prompt_templates(id),
    final_prompt TEXT NOT NULL, -- Actual prompt sent to Gemini
    gemini_response TEXT,
    response_metadata JSONB, -- tokens used, model, temperature
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔧 API Endpoints

### File Upload & Management
- `POST /api/v1/upload` - Upload a document
- `GET /api/v1/documents` - List all documents
- `GET /api/v1/documents/{id}` - Get specific document
- `DELETE /api/v1/documents/{id}` - Delete document
- `GET /api/v1/progress/{file_id}` - SSE endpoint for upload progress

### AI Analysis
- `POST /api/v1/analyze` - Analyze document with prompt
- `GET /api/v1/analyses` - List all analyses
- `GET /api/v1/analyses/{id}` - Get specific analysis

### Prompt Templates
- `GET /api/v1/prompt-templates` - List templates
- `POST /api/v1/prompt-templates` - Create template
- `GET /api/v1/prompt-templates/{id}` - Get template
- `PUT /api/v1/prompt-templates/{id}` - Update template
- `DELETE /api/v1/prompt-templates/{id}` - Delete template
- `POST /api/v1/init-default-templates` - Initialize default templates

### Health Check
- `GET /health` - Application health status

## 🎯 Processing Pipeline

The system implements a 3-stage processing pipeline:

1. **Stage 1**: "Extracting text from document" (20% progress)
   - Actual text extraction from PDF/TXT files
   - Uses PyPDF2 and pdfplumber for robust extraction

2. **Stage 2**: "Preparing for analysis" (60% progress)  
   - Text preparation and language detection
   - Document chunking if needed for large files

3. **Stage 3**: "Ready for AI analysis" (100% progress)
   - Document ready for Gemini AI analysis
   - Available for prompt testing

## 🤖 AI Integration

### Gemini API Implementation
```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

async def analyze_document(prompt: str, document_text: str):
    try:
        response = await model.generate_content_async(
            f"{prompt}\n\nDocument:\n{document_text}"
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise
```

### Default Prompt Templates
The system includes pre-built templates:
- **Executive Summary**: Concise 3-5 bullet point summaries
- **Key Insights**: Extract 5 most important insights
- **Action Items**: List all tasks and next steps
- **Financial Figures**: Extract amounts and percentages

## 🛠️ Development Setup

### Backend Development

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start services (PostgreSQL & Redis)**
   ```bash
   docker-compose up postgres redis -d
   ```

6. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Development

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

## 🎯 Usage Examples

### Uploading a Document
1. Go to the home page or Documents page
2. Drag and drop a PDF or TXT file (max 5MB)
3. Watch real-time progress as the document is processed
4. Once ready, the document appears in your documents list

### Analyzing a Document
1. Navigate to Analysis page
2. Select a document to analyze
3. Choose a pre-built template or write a custom prompt
4. Click "Analyze" to get AI insights
5. View results with copy/export options

### Creating Custom Prompts
1. Go to Templates page
2. Click "New Template"
3. Fill in name, category, and prompt text
4. Use `{document_content}` as placeholder for document text
5. Save and use in analysis

## 🔒 Security Features

- Input validation for file uploads
- File type restrictions (PDF, TXT only)
- File size limits (5MB max)
- Rate limiting on API endpoints (10 requests/minute)
- Environment variable protection for API keys
- CORS configuration for frontend access
- Health checks for container monitoring

## 📊 Performance Features

- Redis caching for AI responses (identical prompt+document pairs)
- Async processing with background tasks
- Connection pooling for database
- Retry logic for external API calls
- Document chunking for large files
- Efficient text extraction with fallback methods
- Real-time progress updates via Server-Sent Events

## 🐛 Troubleshooting

### Common Issues

1. **Gemini API Key Error**
   - Ensure you have a valid API key from Google AI Studio
   - Check that the key is correctly set in your `.env` file

2. **Database Connection Error**
   - Make sure PostgreSQL is running
   - Check database URL in environment variables

3. **File Upload Fails**
   - Verify file is PDF or TXT format
   - Check file size is under 5MB
   - Ensure backend upload directory has write permissions

4. **Real-time Updates Not Working**
   - Check if SSE connections are being blocked by firewall
   - Verify backend is accessible from frontend

### Logs

View application logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
```

## 🚀 Deployment

### Production Deployment

1. **Update environment variables**
   ```bash
   # Set production values
   DATABASE_URL=postgresql://user:password@your-db-host:5432/docanalyzer
   REDIS_URL=redis://your-redis-host:6379
   SECRET_KEY=your-production-secret-key
   ALLOWED_ORIGINS=https://your-domain.com
   ```

2. **Build and deploy**
   ```bash
   docker-compose up --build -d
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@postgres:5432/docanalyzer` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `MAX_FILE_SIZE` | Maximum upload file size | `5242880` (5MB) |
| `RATE_LIMIT_REQUESTS` | Requests per minute limit | `10` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Manual Testing
1. Upload various file types (PDF, TXT)
2. Test real-time progress updates
3. Try different prompt templates
4. Verify AI analysis responses
5. Test rate limiting (>10 requests/minute)

## 📈 Implementation Status

### ✅ Completed Features
- [x] File upload with drag-and-drop interface
- [x] Real-time processing with SSE
- [x] Text extraction from PDF/TXT files
- [x] Google Gemini AI integration
- [x] Prompt template management (CRUD)
- [x] Rate limiting (10 requests/minute)
- [x] Response caching with Redis
- [x] Multi-stage processing pipeline
- [x] Error handling and logging
- [x] Docker containerization
- [x] Health checks
- [x] Responsive UI design

### 🔄 Current Implementation Notes
- AI responses are currently mocked for testing purposes
- Real Gemini API integration is ready but requires valid API key
- All database schemas and endpoints are fully implemented
- Frontend supports all planned features

## 🏗️ Architecture Decisions

1. **FastAPI**: Chosen for async support and automatic API documentation
2. **PostgreSQL**: Robust relational database for complex queries
3. **Redis**: Fast caching for AI responses and session management
4. **React**: Modern frontend with hooks and functional components
5. **Server-Sent Events**: Real-time updates without WebSocket complexity
6. **Docker**: Containerization for easy deployment and development

## ⚠️ Limitations & Assumptions

1. **File Size**: Limited to 5MB per file for performance
2. **File Types**: Only PDF and TXT files supported
3. **Rate Limiting**: 10 requests per minute to prevent API abuse
4. **Token Limits**: Gemini Pro has 32K context window
5. **Caching**: Responses cached by prompt+document hash

## 📝 Time Investment

- **Backend Development**: ~2.5 hours
- **Frontend Development**: ~1.5 hours  
- **AI Integration**: ~1 hour
- **Docker & Deployment**: ~0.5 hours
- **Testing & Documentation**: ~0.5 hours
- **Total**: ~6 hours

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check container logs with `docker-compose logs`

## 📝 License

This project is licensed under the MIT License.

---

**Built with ❤️ using FastAPI, React, and Google Gemini AI**

*This project demonstrates full-stack development skills, AI integration, real-time features, and production-ready practices.* 