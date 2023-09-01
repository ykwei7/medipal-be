from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFDirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
import argparse
from env import OPENAI_API_KEY

import sys

def add_to_vector_db(file="", dir="", init=False):
    if file != "":
        loader = PyPDFLoader(file)
    elif dir != "":
        loader = PyPDFDirectoryLoader(dir)
    else:
        raise ValueError("no input file specified")

    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, 
                                                chunk_overlap=100, 
                                                separators=["\n\n", "\n", " ", ""],
                                                length_function = len)

    text_documents = text_splitter.split_documents(docs)
    print (f'Adding {len(text_documents)} documents')

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    if init:
        vectordb = FAISS.from_documents(text_documents, embeddings)
        vectordb.save_local("faiss_index")
        print("Created new faiss vector store")
    else:
        vectordb = FAISS.load_local("faiss_index", embeddings)
        texts = [d.page_content for d in text_documents]
        metas = [d.metadata for d in text_documents]
        vectordb.add_texts(texts, metas)
        vectordb.save_local("faiss_index")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str)
    parser.add_argument("--dir", type=str)
    args = parser.parse_args()

    if args.file is not None:
        add_to_vector_db(file=args.file, init=False)

    elif args.dir is not None:
        add_to_vector_db(dir=args.dir, init=True)

if __name__ == "__main__":
    main()