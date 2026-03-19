from typing import List

from src.db.db import get_session_context
from src.rag.resource_pool import ResourcePool
import re

class Retriever():
    """ Housing class for all retrieval related operations """

    @staticmethod
    async def gen_retrieval_queries( 
        context_str: str, 
        llm_obj,
        n_research_max=1, 
        n_embed_max=1,
        ):
        """
        Optimizes user query intentions for research paper search engine querying and transcript summary embedding retrieval respectively
        """
        
        query_prompt = f"""
        Based on the user's intention from the provided user context, generate {n_research_max} research paper queries and {n_embed_max} embedding 
        queries that will be used for embedding-based vector similarity retrieval from fitness-science video transcripts, research papers, and textbooks.

        KEY DIFFERENCES:
        1. RESEARCH QUERIES: Scientific terminology for academic papers (e.g., "quadricep", "hypertrophic adaptations")
        2. EMBEDDING QUERIES: Natural coaching language matching video transcript/textbook style

        CORE PRINCIPLES:
        1. PRESERVE INTENT & SCOPE - Do not change what the user is asking about or narrow their question. Do NOT interject your own expertise. Do not make assumptions about specific exercises or methodologies.
        2. ADD SEMANTIC CONTEXT - Include related terminology that appears in fitness content without altering meaning
        3. MAINTAIN SPECIFICITY - If they ask broadly, keep it broad; if specific, keep it specific
        4. USE NATURAL LANGUAGE - Match how fitness coaches and educators actually speak
        5. END WITH SEARCH KEYWORDS - Last token pooling in embedding model carries more weight 

        OUTPUT FORMAT (strict):
        <RESEARCH QUERY> query text here
        <EMBEDDING QUERY> query text here

        EMBEDDING QUERY OPTIMIZATION GUIDELINES:
        1. EXPAND WITH SEMANTIC RICHNESS
        Add context words that commonly co-occur in fitness content without changing the scope.
        
        User Query: "chest exercises"
        Bad: "advanced chest exercises for bodybuilders" ❌ (narrowed scope - added "advanced" and "bodybuilders")
        Good: "exercises and training methods for chest" ✓ (same scope, added retrievable context, last token keyword)

        2. CLARIFY IMPLICIT CONTEXT
        If the query's purpose is clear, make it explicit for better matching.
        
        User Query: "how much protein do I need?"
        Bad: "optimal protein intake timing and amount" ❌ (added timing specificity that the user didn't ask for)
        Good: "optimal amount of required protein" ✓ (clarified likely context without narrowing, last token keyword)

        3. USE COMPLETE CONCEPTS
        Transform technical terms or abbreviations into full phrases that appear in educational content.
        
        User Query: "best ROM"
        Bad: "range of motion benefits" ❌ (not specifically matching best suggestions, vague)
        Good: "exercise best range of motion" ✓ (expanded abbreviation with minimal context, last token keywords)

        4. TRANSFORM KEYWORDS TO FITNESS DOMAIN TERMINOLOGY
        Include fitness-specific synonyms and related terms that help vector matching.
        Be careful here not to randomly interject concepts that the user did not specify.
        
        User Query: "getting stronger"
        Bad: "progressive overload for strength" ❌ (injected specific methodology)
        Bad: "optimal hypertrophy exercises" ❌ (falsely assumed strength is always tied to hypertrophy)
        Bad: "increasing strength on barbell press" ❌ (interjected specific exercise suggestion)
        Good: "increasing performance and building strength" ✓ (added domain terms, same scope)

        RESEARCH QUERY GUIDELINES:
        - Use scientific/Latin terminology: "quadricep activation" not "quad engagement"
        - Include measurable outcomes: "1RM strength gains"
        - Target specific research areas: "concentric versus eccentric range of motion"
        - Use quotes for exact phrases if needed: "resistance training frequency"

        IMPORTANT: Preserve the user's original intent and scope. Add specificity and context, but don't narrow their question or inject domain expertise they didn't ask for.

        Context: {context_str}
        """

        response = await llm_obj.ainvoke(query_prompt)
        research_queries = re.findall(r"<RESEARCH QUERY>\s*(.+)", response.content)
        embedding_queries = re.findall(r"<EMBEDDING QUERY>\s*(.+)", response.content)

        return [q.strip() for q in research_queries], [q.strip() for q in embedding_queries]

    @staticmethod
    async def get_user_data(user_uid: str):
            """ Collects and serializes user data and workout logs """
            
            async with get_session_context() as session:
                user_info = await ResourcePool.user_service.get_user_by_id(user_uid, session)
                # user_logs = await self.workout_logs_service.get_logs_by_user(self.user_uid, session)
                # user_logs_json = []
                # for log in user_logs:
                #     user_logs_json.append(WorkoutLogResponse.model_validate(log).model_dump(mode='json'))

            user_data = {
                "username" : user_info.username,
                "full_name" : user_info.full_name,
                "age" : user_info.age,
                "height_raw" : user_info.height_raw,
                "height_unit" : user_info.height_unit.value if user_info.height_unit else None,
                # "user_workout_logs" : user_logs_json
            }
            return user_data

    @staticmethod
    def retrieve_embedded_chunks(queries: List[str], n_yt_res=10, n_txtbk_res=5) -> dict:
        # Chromadb retrieval
        collection_yt = ResourcePool.chroma_client.get_collection(name="yt_transcripts", embedding_function=ResourcePool.embedder)
        collection_txtbk = ResourcePool.chroma_client.get_collection(name="txtbks", embedding_function=ResourcePool.embedder)
        chunks = {'transcript_chunks': [], 'txtbk_chunks': []}
        for query in queries:
            yt_res = collection_yt.query(query_texts=[f"Instruct: Find relevant documents \n Query: {query}"], n_results=n_yt_res)
            chunks['transcript_chunks'].extend(
                [{'chunk': doc, 'title': metadata['title'], 'vid_id': metadata['vid_id'], 'distance': dist} 
                for doc, metadata, dist in zip(yt_res['documents'][0], yt_res['metadatas'][0], yt_res['distances'][0])]
                )
            txtbk_res = collection_txtbk.query(query_texts=[f"Instruct: Find relevant documents \n Query: {query}"], n_results=n_txtbk_res)
            chunks['txtbk_chunks'].extend(
                [{'chunk': doc, 'title': metadata['source_title'], 'header': metadata['Header_2'], 'distance': dist} 
                for doc, metadata, dist in zip(txtbk_res['documents'][0], txtbk_res['metadatas'][0], txtbk_res['distances'][0])]
                )

        return chunks
    
    @staticmethod
    def retrieve_exa_papers(queries: List[str], n_results=10):
        results = []
        for query in queries:
            response = ResourcePool.exa_client.search_and_contents(
            query.strip(),
            type = "auto",
            category = "research paper",
            summary = True,
            num_results = n_results
            )
            results.extend([
                {
                    'title': paper.title,
                    'url': paper.url,
                    'published_date': paper.published_date,
                    'summary': paper.summary
                }
                for paper in response.results
            ])
        return results