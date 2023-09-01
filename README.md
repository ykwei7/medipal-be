# medipal
To run the code locally, perform the following steps.

### 1. Install all python requirements
    pip install -r requirements.txt

### 2. Generate faiss vector store
    python index.py -dir data

### 3. Create a local mysql instance

### 4. Create .env file to store environment variable
    OPENAI_API_KEY="abcdefg123"
    DB_URL="mysql://root:password@localhost:3306/medipal"

### 5. Start the server
    python app.py
