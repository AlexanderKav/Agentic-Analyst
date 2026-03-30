# Agentic Analyst - Docker Setup

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/agentic-analyst.git
cd agentic-analyst

# 2. Copy environment variables
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Start the app
docker-compose -f docker/docker-compose.yml up -d

# 4. Open http://localhost:8000