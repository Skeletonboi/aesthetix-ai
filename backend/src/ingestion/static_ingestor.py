# ChromaDB requires sqlite3>=3.35.0., so we substitute sqlite3 with pysqlite3 (pip install pysqlite3-binary )
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from pathlib import Path
import re
import uuid
import json
from docling.document_converter import DocumentConverter
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from src.ingestion.utils import ChromaDBLocalGPUEmbedder
from src.config import Config
import chromadb

VDB_PATH = os.path.join(Path(__file__).parents[0], 'chroma_db')
HF_EMBED_MODEL_NAME = Config.HF_EMBED_MODEL_NAME

def chunking_len_function(input_str: str):
    return len(input_str.split(" "))

def embed_nsca_manual():
    source = 'https://www.nsca.com/contentassets/116c55d64e1343d2b264e05aaf158a91/basics_of_strength_and_conditioning_manual.pdf'

    converter = DocumentConverter()
    doc = converter.convert(source).document
    md = doc.export_to_markdown()

    cmd  = re.sub(r'[ \t]{2,}', ' ', md)
    cmd = re.sub(r'^\s*##\s*(Procedure|Coaching Points|Start Position|Starting Position).*', r'\1', cmd, flags=re.MULTILINE | re.IGNORECASE)

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("##", "Header_2"),
        ],
    )

    secondary_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        length_function=chunking_len_function
    )

    splits = splitter.split_text(cmd)
    
    data = {}
    for doc in splits:
        if len(doc.page_content) < 256:
            continue

        final_chunks = []
        n_words = len(doc.page_content.split(' '))
        if n_words < 512:
            final_chunks.append(doc.page_content)
        else:
            # Re-chunk oversized chunks
            sub_splits = secondary_splitter.split_text(doc.page_content)
            for sub_chunk in sub_splits:
                final_chunks.append(sub_chunk)

        for raw_chunk in final_chunks:
            chunk = f'{doc.metadata.get("Header_2", "")}\n' + raw_chunk
            metadata = {
                "Header_2" : doc.metadata.get("Header_2", ""),
                "source_title" : "The National Strength and Conditioning Association's (NSCA) BASICS OF STRENGTH AND CONDITIONING MANUAL",
                "source_author" : "Dr. William A. Sands, Jacob J. Wurth, Dr. Jennifer K. Hewit",
                "source_year" : "2012"}
            id = str(uuid.uuid5(uuid.NAMESPACE_X500, chunk)) # Using uuid5 hash for de-duplication when inserting into ChromaDB
            # Dictionary hashing to de-duplicate (upsert requires de-duplicated input)
            data[id] = (chunk, metadata)
    
    ids = list(data.keys())
    chunks = [data[id][0] for id in ids]
    metadatas = [data[id][1] for id in ids]

    txtbk_data = {
        "ids": ids,
        "chunks": chunks,
        "metadatas": metadatas
    }

    with open(os.path.join(Path(__file__).parents[0], 'post_txtbks', 'ncsa_manual_new.json'), 'w') as f:
        json.dump(txtbk_data, f)

    # _ = vectorize_data(ids, chunks, metadatas)
    
    return

def embed_acsm_txtbk():
    # source = './raw_txtbks/ACSM-Exercise-Testing-and-Prescription.pdf'
    source = os.path.join(Path(__file__).parents[0], 'raw_txtbks', 'ACSM-Exercise-Testing-and-Prescription-11th.pdf')

    converter = DocumentConverter()
    doc = converter.convert(source).document
    md = doc.export_to_markdown()

# Clean up the markdown more thoroughly
    cmd = re.sub(r'\t+', ' ', md)                    # All tabs → single space
    cmd = re.sub(r' {2,}', ' ', cmd)                 # Multiple spaces → single space
    cmd = re.sub(r'\n{3,}', '\n\n', cmd)             # Excessive newlines → double newline
    cmd = cmd.strip()                                # Remove leading/trailing whitespace

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("##", "Header_2"),
        ],
    )

    secondary_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        length_function=chunking_len_function
    )

    splits = splitter.split_text(cmd)
    
    data = {}
    for doc in splits:
        if len(doc.page_content) < 256:
            continue

        final_chunks = []
        n_words = len(doc.page_content.split(' '))
        if n_words < 512:
            final_chunks.append(doc.page_content)
        else:
            # Re-chunk oversized chunks
            sub_splits = secondary_splitter.split_text(doc.page_content)
            for sub_chunk in sub_splits:
                final_chunks.append(sub_chunk)

        for raw_chunk in final_chunks:
            chunk = f'{doc.metadata.get("Header_2", "")}\n' + raw_chunk
            metadata = {
                "Header_2" : doc.metadata.get("Header_2", ""),
                "source_title" : "ACSM's Guidelines for Exercise Testing and Prescription Eleventh Edition",
                "source_author" : "Gary Liguori, Yuri Feito, Charles Fountaine, Brad A. Roy",
                "source_year" : "2022"}
            id = str(uuid.uuid5(uuid.NAMESPACE_X500, chunk)) # Using uuid5 hash for de-duplication when inserting into ChromaDB
            # Dictionary hashing to de-duplicate (upsert requires de-duplicated input)
            data[id] = (chunk, metadata)
    
    ids = list(data.keys())
    chunks = [data[id][0] for id in ids]
    metadatas = [data[id][1] for id in ids]

    txtbk_data = {
        "ids": ids,
        "chunks": chunks,
        "metadatas": metadatas
    }

    with open(os.path.join(Path(__file__).parents[0], 'post_txtbks', 'acsm_txtbk_new.json'), 'w') as f:
        json.dump(txtbk_data, f)

    # f_ids, f_chunks, f_metadatas = [], [], []
    # for i, obj in enumerate(zip(ids, chunks, metadatas)):
    #     if len(obj[1]) < 7086:
    #         f_ids.append(obj[0])
    #         f_chunks.append(obj[1])
    #         f_metadatas.append(obj[2])
    # vectorize_data(f_ids, f_chunks, f_metadatas)
    # _ = vectorize_data(ids, chunks, metadatas)
    return

def embed_ncsa_txtbk():
    source = os.path.join(Path(__file__).parents[0], 'raw_txtbks', '_OceanofPDF.com_Essentials_of_strength_training_and_conditioning_fourth_edition_-_G_Gregory_Haff.pdf')

    converter = DocumentConverter()
    doc = converter.convert(source).document
    md = doc.export_to_markdown()

# Clean up the markdown more thoroughly
    cmd = re.sub(r'\t+', ' ', md)                    # All tabs → single space
    cmd = re.sub(r' {2,}', ' ', cmd)                 # Multiple spaces → single space
    cmd = re.sub(r'\n{3,}', '\n\n', cmd)             # Excessive newlines → double newline
    cmd = cmd.strip()                                # Remove leading/trailing whitespace

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("##", "Header_2"),
        ],
    )

    secondary_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        length_function=chunking_len_function
    )

    splits = splitter.split_text(cmd)
    
    data = {}
    for doc in splits:
        if len(doc.page_content) < 256:
            continue

        final_chunks = []
        n_words = len(doc.page_content.split(' '))
        if n_words < 512:
            final_chunks.append(doc.page_content)
        else:
            # Re-chunk oversized chunks
            sub_splits = secondary_splitter.split_text(doc.page_content)
            for sub_chunk in sub_splits:
                final_chunks.append(sub_chunk)

        for raw_chunk in final_chunks:
            chunk = f'{doc.metadata.get("Header_2", "")}\n' + raw_chunk
            metadata = {
                "Header_2" : doc.metadata.get("Header_2", ""),
                "source_title" : "NSCA Essentials of Strength Training and Conditioning Fourth Edition",
                "source_author" : "G. Gregory Haff, N. Travis Triplett",
                "source_year" : "2016"}
            id = str(uuid.uuid5(uuid.NAMESPACE_X500, chunk))
            # Dictionary hashing to de-duplicate (upsert requires de-duplicated input)
            data[id] = (chunk, metadata)

    ids = list(data.keys())
    chunks = [data[id][0] for id in ids]
    metadatas = [data[id][1] for id in ids]

    txtbk_data = {
        "ids": ids,
        "chunks": chunks,
        "metadatas": metadatas
    }
    with open(os.path.join(Path(__file__).parents[0], 'post_txtbks', 'ncsa_txtbk_new.json'), 'w') as f:
        json.dump(txtbk_data, f)

    # _ = vectorize_data(ids, chunks, metadatas)
    return

def all_vectorize():
    
    sources = [
        os.path.join(Path(__file__).parents[0], 'post_txtbks', 'ncsa_manual_new.json'),
        os.path.join(Path(__file__).parents[0], 'post_txtbks', 'ncsa_txtbk_new.json'),
        os.path.join(Path(__file__).parents[0], 'post_txtbks', 'acsm_txtbk_new.json')
    ]
    client = chromadb.PersistentClient(path=VDB_PATH)
    collection = client.create_collection(name="txtbks",
                                        embedding_function=ChromaDBLocalGPUEmbedder(HF_EMBED_MODEL_NAME, device="cuda"),
                                        get_or_create=True)

    for source in sources:
        with open(source, 'r') as f:
            data = json.load(f)
            collection.upsert(
                ids=data['ids'],
                documents=data['chunks'],
                metadatas=data['metadatas']
            )
    return

all_vectorize()

# embed_nsca_manual()
# embed_acsm_txtbk()
# embed_ncsa_txtbk()