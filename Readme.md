Trước khi chạy dự án, cần cài đặt:

Python 3.12 sử dụng anaconda hoặc venv để run

Download dependence qua requirements.txt có ở cả fontend và backend để download dependence
cho dự án

Cần xây dựng ollama local trên máy cá nhân 

### Download ollama
##### Trên os hoặc linux 
curl -fsSL https://ollama.com/install.sh | sh

##### Trên windown có thể tải thông qua
https://ollama.com/download


Sau khi cài đặt ollama cần pull model (ollama pull qwen3)

Với backend cần chạy python.py khi đã add đủ dependence và run
bằng python.py hoặc uvicorn run main:app --port

Với frontend run steamlit run app:app --port

### Note 
Cần có các trường .env riêng cho frontend và backend đã config trong file .env
vì không có trường nào ảnh hưởng lớn nên em xin add vào đây

### Backend .env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3
EMBEDDING_MODEL=nomic-embed-text

# Database Configuration
DATABASE_URL=sqlite:///./data/employees.db

# ChromaDB Configuration
CHROMA_DIR=chroma_db
COLLECTION_NAME=financial_docs

# App Configuration
DEBUG=true
PORT=8000
MAX_UPLOAD_SIZE=10485760
ALLOWED_ORIGINS=*

### fontend.env
BACKEND_URL=http://localhost:8000