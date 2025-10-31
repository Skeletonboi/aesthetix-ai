from typing import List

from src.db.db import get_session_context
from src.rag.resource_pool import ResourcePool

class Retriever():
    """ Housing class for all retrieval related operations """

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